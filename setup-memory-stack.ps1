# ==============================================================================
# Ultimate Memory Stack v4.0.1 - top-level installer (Windows / PowerShell)
# Apache-2.0 (C) 2026 esoteric1entity. A PDuk Brainworks project.
# ==============================================================================
#
# Usage (run from the directory where the stack should live, or use -Target):
#   .\setup-memory-stack.ps1                              # default: general-edition + all addons
#   .\setup-memory-stack.ps1 -Minimal                     # core only
#   .\setup-memory-stack.ps1 -Addon memory-graphiti       # core + selected
#   .\setup-memory-stack.ps1 -Addon memory-vault,memory-graphiti
#   .\setup-memory-stack.ps1 -NoTemplater                 # skip Obsidian Templater auto-enable
#   .\setup-memory-stack.ps1 -Edition general
#   .\setup-memory-stack.ps1 -Target C:\my-workspace      # install somewhere else
#   .\setup-memory-stack.ps1 -Yes                         # non-interactive (accept defaults)
#
# Pass-through:
#   -Compliance, -Extensions, -MigrateFrom, -SkipWizard
#
# Requires PowerShell 5.1+ and Python 3.8+ (the core install delegates to setup.py).
# ==============================================================================

[CmdletBinding()]
param(
    [string]$Edition = "general",
    [switch]$Minimal,
    [string[]]$Addon = @(),
    [switch]$NoTemplater,
    [string]$Target = "",
    [switch]$Yes,
    [string]$Compliance,
    [string]$Extensions,
    [string]$MigrateFrom,
    [switch]$SkipWizard,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
# Version is single-sourced from the package-root VERSION file (#14 fix)
$VersionFile = Join-Path $ScriptDir "VERSION"
if (Test-Path $VersionFile) {
    $StackVersion = (Get-Content $VersionFile -Raw).Trim()
} else {
    $StackVersion = "4.0.1"
}

if ($Help) {
    Get-Content $MyInvocation.MyCommand.Definition | Select-Object -First 20 | Select-Object -Skip 1
    exit 0
}

$NonInteractive = $Yes -or [Console]::IsInputRedirected

# ---------- target resolution (DETECT + CONFIRM) ----------
$OpenClawWs = Join-Path $env:USERPROFILE ".openclaw\workspace"

if (-not $Target) {
    $Target = (Get-Location).Path
    if (-not $NonInteractive) {
        Write-Host "[>] Where should the memory stack be installed?"
        $defaultChoice = "1"
        Write-Host "    [1] Current directory:           $Target"
        if (Test-Path $OpenClawWs) {
            Write-Host "    [2] OpenClaw workspace (found):  $OpenClawWs"
        }
        Write-Host "    [3] Custom path"
        if ([string]::Equals($Target.TrimEnd('\'), $ScriptDir.TrimEnd('\'), 'OrdinalIgnoreCase')) {
            Write-Host "  [!] The current directory is the package itself - installing here would mix" -ForegroundColor Yellow
            Write-Host "      your memory data into the package tree (and into its git history)." -ForegroundColor Yellow
            $defaultChoice = if (Test-Path $OpenClawWs) { "2" } else { "3" }
        }
        $choice = Read-Host "  Choice [$defaultChoice]"
        if (-not $choice) { $choice = $defaultChoice }
        switch ($choice) {
            "1" { $Target = (Get-Location).Path }
            "2" { $Target = $OpenClawWs }
            "3" { $Target = Read-Host "  Path" }
            default { Write-Host "[X] Invalid choice" -ForegroundColor Red; exit 1 }
        }
    }
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
$Target = (Resolve-Path $Target).Path

# Guard: never install into the package itself without explicit consent
if ([string]::Equals($Target.TrimEnd('\'), $ScriptDir.TrimEnd('\'), 'OrdinalIgnoreCase')) {
    if (-not $NonInteractive) {
        $confirm = Read-Host "  [!] Really install INTO the package directory itself? [y/N]"
        if ($confirm -notin @("y", "Y")) {
            Write-Host "Aborted - run from your working directory, or pass -Target <dir>."
            exit 1
        }
    } else {
        Write-Host "[X] Refusing to install into the package directory itself ($ScriptDir)." -ForegroundColor Red
        Write-Host "    Run from your working directory, or pass -Target <dir>." -ForegroundColor Red
        exit 1
    }
}

# Existing-install handling (memory/ data is never touched by a re-install)
$manifestPath = Join-Path $Target ".ums-manifest.json"
if ((Test-Path $manifestPath) -or (Test-Path (Join-Path $Target "memory"))) {
    Write-Host "[i] Existing install detected at $Target"
    $scaffold = Join-Path $Target "ultimate-memory-stack"
    if (Test-Path (Join-Path $scaffold "common-specs")) {
        if (-not $NonInteractive) {
            $refresh = Read-Host "    Refresh the scaffolded specs in place? memory/ data is not touched. [Y/n]"
            if ($refresh -in @("n", "N")) { Write-Host "Aborted - nothing changed."; exit 1 }
        }
        Remove-Item -Recurse -Force $scaffold
        Write-Host "    [~] Scaffolded spec tree refreshed (memory/ untouched)."
    }
    Write-Host "    (Upgrading from a v2.0 deployment? Use -MigrateFrom v2.0 instead.)"
}

$env:WORKING_DIR = $Target
# Option C: signal the edition setup that the top-level installer owns the final
# "Next steps" summary, so the edition layer (and its Python delegate) suppress theirs.
$env:UMS_PARENT = "1"

# ---------- harness detection (BEFORE we create anything) ----------
$Harness = "generic"
if (((Test-Path (Join-Path $Target "AGENTS.md")) -and (Test-Path (Join-Path $Target "SOUL.md"))) -or
    [string]::Equals($Target.TrimEnd('\'), $OpenClawWs.TrimEnd('\'), 'OrdinalIgnoreCase')) {
    $Harness = "openclaw"
} elseif (Test-Path (Join-Path $Target ".claude")) {
    $Harness = "claude-code"
}

# ---------- precondition checks ----------
$EditionDir = Join-Path $ScriptDir "$Edition-edition"
if (-not (Test-Path $EditionDir)) {
    Write-Host "[X] Edition '$Edition' not found at $EditionDir" -ForegroundColor Red
    Write-Host "    Available editions:" -ForegroundColor Yellow
    Get-ChildItem -Path $ScriptDir -Directory -Filter "*-edition" | ForEach-Object {
        Write-Host "      - $($_.Name)" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host ""
Write-Host "[>] Ultimate Memory Stack v$StackVersion - $Edition-edition install" -ForegroundColor Cyan
Write-Host "    Install target: $Target"
Write-Host ""

# Build pass-through args for the edition setup.
# MUST be a hashtable (named splatting) — array splatting binds positionally in
# PowerShell, which would feed the literal string "-Compliance" into $Compliance.
$PassThrough = @{}
if ($Compliance)  { $PassThrough.Compliance  = $Compliance }
if ($Extensions)  { $PassThrough.Extensions  = $Extensions }
if ($MigrateFrom) { $PassThrough.MigrateFrom = $MigrateFrom }
if ($SkipWizard)  { $PassThrough.SkipWizard  = $true }

# Run the edition's setup.ps1 by absolute path WITHOUT changing location.
& (Join-Path $EditionDir "setup.ps1") @PassThrough
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[X] Edition setup failed (exit $LASTEXITCODE) - aborting before addon registration" -ForegroundColor Red
    exit $LASTEXITCODE
}

# ---------- addon registration ----------
$Registered = @()
$RegisteredSkills = @()
if ($Minimal) {
    Write-Host ""
    Write-Host "[~] Skipping addons (-Minimal). Base install complete." -ForegroundColor Yellow
    Write-Host "    To install addons later:  .\setup-memory-stack.ps1 -Addon <name>"
} else {
    if ($Addon.Count -eq 0) {
        $Addon = @("memory-vault", "memory-graphiti", "memory-graphify", "memory-llmlingua")
    }

    $AddonMap = @{
        "memory-vault"     = "recommended-addons\obsidian-vault-config"
        "memory-graphiti"  = "recommended-addons\graphiti-installer"
        "memory-graphify"  = "recommended-addons\graphify-installer"
        "memory-llmlingua" = "recommended-addons\llmlingua-installer"
    }

    $SkillsDir = Join-Path $Target ".claude\skills"
    New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null

    Write-Host ""
    Write-Host "[>] Registering addons (Claude Code Skills)" -ForegroundColor Cyan

    # Claude Code discovers skills as .claude\skills\<name>\SKILL.md, where
    # <name> is the SKILL.md frontmatter `name:` field. (#12 fix, 2026-06-11:
    # the previous flat install-<addon>.md copies were never discoverable.)
    foreach ($a in $Addon) {
        $relDir = $AddonMap[$a]
        if (-not $relDir) {
            Write-Host "  [!] Unknown addon: $a (skipping)" -ForegroundColor Yellow
            continue
        }
        $src = Join-Path $ScriptDir "$relDir\SKILL.md"
        if (-not (Test-Path $src)) {
            Write-Host "  [!] Skill file not found for $a at $src (skipping)" -ForegroundColor Yellow
            continue
        }
        # Capture the match BEFORE dereferencing it. Chaining
        # `(Select-String ...).Matches.Groups[1].Value.Trim()` on a SKILL.md with no
        # `name:` line dies at the `[1]` INDEX — Select-String returns nothing,
        # `.Matches` yields $null, and PS 5.1 raises NullArray, "Cannot index into a
        # null array" (measured; it never reaches .Trim()). With
        # $ErrorActionPreference = Stop that ABORTS the installer, so the guard below
        # was unreachable dead code and the operator got a PowerShell stack trace
        # instead of the one-line skip the bash door prints.
        $nameMatch = Select-String -Path $src -Pattern '^name:\s*(.+)$' | Select-Object -First 1
        $skillName = if ($nameMatch) { $nameMatch.Matches.Groups[1].Value.Trim() } else { "" }
        if (-not $skillName) {
            Write-Host "  [!] ${a}: SKILL.md has no name: frontmatter (skipping)" -ForegroundColor Yellow
            continue
        }
        $skillDir = Join-Path $SkillsDir $skillName
        New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
        $dest = Join-Path $skillDir "SKILL.md"
        # Copy the ENTIRE addon payload, not just SKILL.md. (2026-08-19 fix —
        # parity with setup-memory-stack.sh.) The skills instruct the user to
        # run `pip install -r <path-to-this-skill>/requirements.txt`,
        # `pip-audit --requirement ...`, and `python .../smoke_test.py`;
        # copying only SKILL.md left every one of those paths dangling.
        # __pycache__ and dotfiles are skipped; nothing is deleted.
        $srcRoot = (Resolve-Path (Join-Path $ScriptDir $relDir)).Path
        Get-ChildItem -Path $srcRoot -Recurse -File |
            Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and $_.Name -notlike '.*' } |
            ForEach-Object {
                # NOTE: PowerShell variables are CASE-INSENSITIVE and a ForEach-Object
                # script block runs in the CALLER's scope — so naming these `$target`
                # or `$rel` would overwrite the script's own `$Target` (the install
                # directory) and corrupt everything after this loop: the post-install
                # protocol copy, the "Workspace:" summary, and the verify.sh command
                # printed for the user. Deliberately distinct names.
                $addonRelPath = $_.FullName.Substring($srcRoot.Length).TrimStart('\')
                $addonDestFile = Join-Path $skillDir $addonRelPath
                New-Item -ItemType Directory -Force -Path (Split-Path $addonDestFile -Parent) | Out-Null
                Copy-Item -Path $_.FullName -Destination $addonDestFile -Force
            }
        # Shared add-on tool, copied in so the installed skill is self-contained
        # (parity with setup-memory-stack.sh). preflight.py detects this layout.
        $preflight = Join-Path $ScriptDir "recommended-addons\preflight.py"
        if ((Test-Path $preflight) -and (Test-Path (Join-Path $srcRoot "requirements.txt"))) {
            Copy-Item -Path $preflight -Destination (Join-Path $skillDir "preflight.py") -Force
        }
        if ($NoTemplater -and $a -eq "memory-vault") {
            # Appended AFTER the body — prepending broke the YAML frontmatter.
            Add-Content -Path $dest -Value "`r`n<!-- Installed with -NoTemplater: skip the Templater community-plugins auto-enable step. -->"
            Write-Host "  [+] $a -> /$skillName (Templater auto-enable skipped)" -ForegroundColor Green
        } else {
            Write-Host "  [+] $a -> /$skillName" -ForegroundColor Green
        }
        $Registered += $a
        $RegisteredSkills += $skillName
    }
}

# ---------- harness registration ----------
$RegNote = "none"
$protocolSrc = Join-Path $Target "ultimate-memory-stack\common-specs\MEMORY_PROTOCOL.md"
$protocolExtendedSrc = Join-Path $Target "ultimate-memory-stack\common-specs\MEMORY_PROTOCOL_EXTENDED.md"
if (Test-Path $protocolSrc) {
    $rulesDir = Join-Path $Target ".claude\rules"
    New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null
    Copy-Item -Path $protocolSrc -Destination (Join-Path $rulesDir "memory_protocol.md") -Force
    $RegNote = ".claude/rules/memory_protocol.md"
}
if (Test-Path $protocolExtendedSrc) {
    $memoryDir = Join-Path $Target "memory"
    New-Item -ItemType Directory -Force -Path $memoryDir | Out-Null
    Copy-Item -Path $protocolExtendedSrc -Destination (Join-Path $memoryDir "MEMORY_PROTOCOL_EXTENDED.md") -Force
}

# ---------- install manifest ----------
$installedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$addonJson = ($Registered | ForEach-Object { '"' + $_ + '"' }) -join ", "
$minimalJson = if ($Minimal) { "true" } else { "false" }
$sourceJson = $ScriptDir -replace '\\', '/'
$manifestJson = @"
{
  "package": "ultimate-memory-stack",
  "version": "$StackVersion",
  "edition": "$Edition",
  "installed_at": "$installedAt",
  "install_door": "script",
  "harness_detected": "$Harness",
  "minimal": $minimalJson,
  "addons": [$addonJson],
  "source_package": "$sourceJson",
  "registered": "$RegNote"
}
"@
# NOTE: written via .NET, NOT `Set-Content -Encoding UTF8`. On Windows PowerShell
# 5.1 that switch emits a UTF-8 BOM, and a leading BOM makes `json.loads()` fail
# outright with "Expecting value: line 1 column 1" — so the bash door produced a
# parseable manifest and this door did not. PS 5.1 has no `utf8NoBOM` encoding, so
# the portable fix is UTF8Encoding($false). `$manifestPath` is absolute (`$Target`
# is Resolve-Path'd above), which matters because .NET resolves relative paths
# against the process working directory, not PowerShell's current location.
#
# The trailing newline is explicit: `Set-Content` appended one and WriteAllText
# does not, and a here-string does not include one after its last line. Dropping
# it would leave this door emitting a file with no final newline while the bash
# door emits one — a gratuitous cross-door difference in a file we tell people is
# machine-readable, and a file POSIX tools consider malformed.
[System.IO.File]::WriteAllText($manifestPath, $manifestJson + "`r`n", (New-Object System.Text.UTF8Encoding $false))

# ---------- summary ----------
Write-Host ""
Write-Host "[OK] Ultimate Memory Stack v$StackVersion - install complete" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:"
Write-Host "  Edition:    $Edition"
Write-Host "  Addons:     $(if ($Registered.Count) { $Registered -join ', ' } else { 'none' })"
Write-Host "  Workspace:  $Target"
Write-Host "  Harness:    $Harness"
Write-Host "  Registered: $RegNote"
Write-Host "  Manifest:   .ums-manifest.json"
Write-Host ""
Write-Host "Next steps:"
$step = 1
Write-Host "  $step. Open your agent harness in this directory"; $step++
if ($RegisteredSkills.Count -gt 0) {
    Write-Host "  $step. Invoke each addon Skill to complete its install:"; $step++
    foreach ($s in $RegisteredSkills) {
        Write-Host "       /$s"
    }
}
# Forward slashes + quotes, because this command is copied into BASH, not PowerShell.
# `bash C:\pkg\verify.sh C:\my ws` is unusable there twice over: bash treats each
# backslash as an escape and silently eats it (`C:pkgverify.sh`), and an unquoted
# path splits on spaces. Git Bash accepts drive-letter paths with forward slashes.
$verifyScriptArg = ($ScriptDir -replace '\\', '/').TrimEnd('/') + "/verify.sh"
$verifyTargetArg = ($Target -replace '\\', '/').TrimEnd('/')
Write-Host "  $step. Validate the install:  bash `"$verifyScriptArg`" `"$verifyTargetArg`"   (Git Bash / WSL)"
if ($Harness -eq "openclaw") {
    Write-Host ""
    Write-Host "  OpenClaw workspace detected - for deep integration (9 root files), run the"
    Write-Host "  OpenClaw adapter: see core\openclaw-adapter\QUICKSTART.md in the cloned package"
} elseif ($Harness -eq "generic") {
    Write-Host ""
    Write-Host "  Using another harness? Point it at memory/ + the protocol from your AGENTS.md -"
    Write-Host "  see INSTALL_AGENT.md in the package for the harness-agnostic wiring steps."
}
Write-Host ""
