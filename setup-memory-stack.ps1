# ==============================================================================
# Ultimate Memory Stack v3.6.0 - top-level installer (Windows / PowerShell)
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
    $StackVersion = "3.6.0"
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
        $skillName = (Select-String -Path $src -Pattern '^name:\s*(.+)$' | Select-Object -First 1).Matches.Groups[1].Value.Trim()
        if (-not $skillName) {
            Write-Host "  [!] ${a}: SKILL.md has no name: frontmatter (skipping)" -ForegroundColor Yellow
            continue
        }
        $skillDir = Join-Path $SkillsDir $skillName
        New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
        $dest = Join-Path $skillDir "SKILL.md"
        Copy-Item -Path $src -Destination $dest -Force
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
if (Test-Path $protocolSrc) {
    $rulesDir = Join-Path $Target ".claude\rules"
    New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null
    Copy-Item -Path $protocolSrc -Destination (Join-Path $rulesDir "memory_protocol.md") -Force
    $RegNote = ".claude/rules/memory_protocol.md"
}

# ---------- install manifest ----------
$installedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$addonJson = ($Registered | ForEach-Object { '"' + $_ + '"' }) -join ", "
$minimalJson = if ($Minimal) { "true" } else { "false" }
$sourceJson = $ScriptDir -replace '\\', '/'
@"
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
"@ | Set-Content -Path $manifestPath -Encoding UTF8

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
Write-Host "  $step. Validate the install:  bash $ScriptDir\verify.sh $Target   (Git Bash / WSL)"
if ($Harness -eq "openclaw") {
    Write-Host ""
    Write-Host "  OpenClaw workspace detected - for deep integration (9 root files), run the"
    Write-Host "  OpenClaw adapter: see ultimate-memory-stack\core\openclaw-adapter\"
} elseif ($Harness -eq "generic") {
    Write-Host ""
    Write-Host "  Using another harness? Point it at memory/ + the protocol from your AGENTS.md -"
    Write-Host "  see INSTALL_AGENT.md in the package for the harness-agnostic wiring steps."
}
Write-Host ""
