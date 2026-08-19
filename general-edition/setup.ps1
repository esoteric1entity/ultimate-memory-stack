# Ultimate Memory Stack — General-Edition Setup (Windows PowerShell)
# Version: 1.1 — 2026-06-16
# Tier: T2+ (PowerShell 5.1+; Python 3.8+ for full functionality)
# Author: see /AUTHORS.md
# License: Apache-2.0

#Requires -Version 5.1

# CmdletBinding forces strict parameter validation — without it, PowerShell
# silently accepts and ignores an unrecognized switch (e.g. a typo, or a flag
# that doesn't exist here yet) rather than erroring, which previously made
# `-DryRun` (before it existed as a real parameter below) a silent no-op that
# ran the real migration instead of refusing — step-8 adversarial round.
[CmdletBinding()]
param(
    [string]$Compliance = "none",
    [string]$Extensions = "",
    [string]$MigrateFrom = "",
    [string]$BackupLocation = "",
    [string]$ChangePreset = "",
    [switch]$DryRun,
    [switch]$Verify,
    [switch]$Status,
    [switch]$GenerateHmacSecret,
    [switch]$SkipWizard,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Configuration
$Edition = "general"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Version is single-sourced from the package-root VERSION file (#14 fix —
# this banner previously said a hardcoded "3.0" on a 3.6.0 release).
$VersionFile = Join-Path $ScriptDir "..\VERSION"
if (Test-Path $VersionFile) {
    $StackVersion = (Get-Content $VersionFile -Raw).Trim()
} else {
    $StackVersion = "4.0.1"
}
$CommonSpecsDir = Join-Path $ScriptDir "..\common-specs"
$WorkingDir = if ($env:WORKING_DIR) { $env:WORKING_DIR } else { Get-Location }

if ($Help) {
    Write-Host "Ultimate Memory Stack - General-Edition Setup (PowerShell)"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\setup.ps1                                                # Fresh install with wizard"
    Write-Host "  .\setup.ps1 -Compliance none                               # Fresh install with preset"
    Write-Host "  .\setup.ps1 -Compliance enterprise -Extensions soc2,gdpr   # Multi-regime"
    Write-Host "  .\setup.ps1 -MigrateFrom v2.0                              # Migrate from v2.0"
    Write-Host "  .\setup.ps1 -MigrateFrom v3.6                              # Migrate from v3.6.x to v4.0.0"
    Write-Host "  .\setup.ps1 -MigrateFrom v3.6 -DryRun                      # Preview the v3.6 migration, no writes"
    Write-Host "  .\setup.ps1 -ChangePreset enterprise                       # Change preset on existing deploy"
    Write-Host "  .\setup.ps1 -Verify                                        # Self-test"
    Write-Host "  .\setup.ps1 -Status                                        # Show state"
    Write-Host "  .\setup.ps1 -GenerateHmacSecret                            # Generate HMAC secret (T3+)"
    Write-Host ""
    Write-Host "Compliance presets: none | enterprise | custom   (PHI/healthcare = reserved value, not available)"
    Write-Host "Extensions: gdpr | soc2 | pci-dss (comma-separated)"
    Write-Host ""
    Write-Host "Note: Delegates to setup.py for most operations."
    Write-Host "      Install Python 3.8+ for full functionality."
    Write-Host ""
    Write-Host "See INSTALL.md for details."
    exit 0
}

# PHI/healthcare is a reserved value — refuse it
# BEFORE delegating to setup.py, so the Windows path fails fast with a clear message
# instead of a confusing downstream exit. Mirrors setup.sh.
if ($Compliance -in @("healthcare")) {
    Write-Host "X ERROR: PHI/healthcare compliance is not available in this edition; 'healthcare' is a reserved preset value. Use 'enterprise' or 'custom'." -ForegroundColor Red
    Write-Host "  The general-edition does not ship PHI/HIPAA compliance. See CONTRIBUTING.md."
    exit 1
}

# Validate compliance preset
$validPresets = @("none", "enterprise", "custom")
if ($Compliance -notin $validPresets) {
    Write-Host "X Invalid compliance preset: $Compliance" -ForegroundColor Red
    Write-Host "  Valid: $($validPresets -join ' | ')"
    exit 1
}

# Validate extensions
$validExtensions = @("gdpr", "soc2", "pci-dss")
if ($Extensions) {
    $extList = $Extensions -split ","
    foreach ($ext in $extList) {
        $ext = $ext.Trim()
        if ($ext -notin $validExtensions) {
            Write-Host "X Invalid extension: $ext" -ForegroundColor Red
            Write-Host "  Valid: $($validExtensions -join ' | ')"
            exit 1
        }
    }
}

# Detect Python
$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "X Python 3.8+ not found in PATH" -ForegroundColor Red
    Write-Host "  Install Python and re-run this script."
    Write-Host "  Alternative: use the manual install method in INSTALL.md"
    exit 1
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Ultimate Memory Stack - General-Edition" -ForegroundColor Cyan
Write-Host "Version: $StackVersion" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Working directory: $WorkingDir"
Write-Host "Python: $pythonCmd"
Write-Host "Compliance preset: $Compliance"
if ($Extensions) {
    Write-Host "Extensions: $Extensions"
}
Write-Host ""

# Delegate to setup.py
$setupPy = Join-Path $ScriptDir "setup.py"
$env:PYTHONIOENCODING = "utf-8"  # Windows consoles default to cp1252; setup.py prints unicode glyphs

$pythonArgs = @($setupPy)
$pythonArgs += "--working-dir"
$pythonArgs += $WorkingDir
$pythonArgs += "--compliance"
$pythonArgs += $Compliance

if ($Extensions) {
    $pythonArgs += "--extensions"
    $pythonArgs += $Extensions
}
if ($Verify) { $pythonArgs += "--verify" }
if ($Status) { $pythonArgs += "--status" }
if ($GenerateHmacSecret) { $pythonArgs += "--generate-hmac-secret" }
if ($MigrateFrom) {
    $pythonArgs += "--migrate-from"
    $pythonArgs += $MigrateFrom
}
if ($DryRun) { $pythonArgs += "--dry-run" }
if ($BackupLocation) {
    $pythonArgs += "--backup-location"
    $pythonArgs += $BackupLocation
}
if ($ChangePreset) {
    $pythonArgs += "--change-preset"
    $pythonArgs += $ChangePreset
}

# Option C: the Python delegate must NOT print its own "Next steps" — this PS
# wrapper owns the single summary. Capture whether WE were parented (the
# top-level installer set UMS_PARENT) before claiming parenthood over Python.
$parented = ($env:UMS_PARENT -eq "1")
$env:UMS_PARENT = "1"

# Run
& $pythonCmd $pythonArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "X Setup failed (exit code $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

if (-not $parented -and -not $Verify -and -not $Status -and -not $GenerateHmacSecret -and -not $ChangePreset) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Setup complete (via Python delegation)" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Open your agent harness in $WorkingDir (e.g. Claude Code or OpenClaw)"
    Write-Host "  2. Paste the activation prompt from:"
    Write-Host "     $WorkingDir\ultimate-memory-stack\common-specs\BOOTSTRAP_PROMPT.md"
    Write-Host "  3. Answer setup wizard"
    Write-Host ""
    Write-Host "To change preset later: .\setup.ps1 -ChangePreset <new>"
}

exit 0
