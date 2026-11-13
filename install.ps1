<#
.SYNOPSIS
    Installs convert-md for the current user from this folder.

.DESCRIPTION
    1. Checks for Python 3.11 or newer (python.org build).
    2. Installs convert-md and its libraries with pip.
    3. Offers to install AutoHotkey v2 (needed only for the Ctrl+Alt+M hotkey).
    4. Adds the right-click menus and the hotkey (convert-md setup).
    5. Runs a test conversion and an installation check.
    No administrator rights are needed. Run it again at any time to update or repair.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install.ps1

.EXAMPLE
    .\install.ps1 -NoHotkey        # right-click menus only
#>
[CmdletBinding()]
param(
    [switch]$NoHotkey,
    [switch]$NoMenus,
    [switch]$Yes,                  # install AutoHotkey without asking, if it's missing
    [string]$Hotkey = '^!m',       # AutoHotkey notation: ^ Ctrl, ! Alt, + Shift, # Win
    [switch]$SkipTest
)

# Not 'Stop': Windows PowerShell 5.1 can turn harmless messages that pip and Python write to
# stderr into terminating errors. Native commands are checked through $LASTEXITCODE instead.
$ErrorActionPreference = 'Continue'

function Step([string]$Text) { Write-Host "`n== $Text" -ForegroundColor Cyan }
function Fail([string]$Text) { Write-Host "`n$Text" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------- 1. Python
Step 'Checking Python'
$PyExe = $null
$PyArgs = @()
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($python -and $python.Source -notlike '*\WindowsApps\*') {
    $PyExe = $python.Source
} elseif (Get-Command py.exe -ErrorAction SilentlyContinue) {
    $PyExe = 'py'; $PyArgs = @('-3')
}
if (-not $PyExe) {
    Fail @'
Python is not installed (the Microsoft Store placeholder doesn't count).
Install the python.org build, open a new PowerShell window, and run this script again:

    winget install --id Python.Python.3.12 -e --scope user

If typing "python" opens the Microsoft Store, turn that off in
Settings > Apps > Advanced app settings > App execution aliases.
'@
}
& $PyExe @PyArgs -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) {
    Fail 'convert-md needs Python 3.11 or newer:  winget install --id Python.Python.3.12 -e --scope user'
}
& $PyExe @PyArgs -c "import sys; print('   Python', sys.version.split()[0], '-', sys.executable)"

# ---------------------------------------------------------------- 2. Package
Step 'Installing convert-md and its libraries (this can take a minute)'
& $PyExe @PyArgs -m pip install --upgrade --disable-pip-version-check --quiet $PSScriptRoot
if ($LASTEXITCODE -ne 0) { Fail 'pip could not install convert-md (see the messages above).' }

# ---------------------------------------------------------------- 3. AutoHotkey
if (-not $NoHotkey) {
    $haveAhk = (Test-Path 'Registry::HKEY_CURRENT_USER\Software\Classes\.ahk') -or
               (Test-Path 'Registry::HKEY_LOCAL_MACHINE\Software\Classes\.ahk')
    if (-not $haveAhk) {
        Step 'AutoHotkey'
        if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
            Write-Warning 'AutoHotkey v2 is not installed and winget is unavailable; skipping the hotkey.'
            $NoHotkey = $true
        } else {
            $answer = if ($Yes) { 'y' } else {
                Read-Host 'The Ctrl+Alt+M hotkey needs AutoHotkey v2. Install it now with winget? [Y/n]' }
            if ($answer -eq '' -or $answer -match '^[Yy]') {
                winget install --id AutoHotkey.AutoHotkey -e --accept-source-agreements --accept-package-agreements
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning 'AutoHotkey did not install; continuing without the hotkey.'
                    $NoHotkey = $true
                }
            } else {
                $NoHotkey = $true
            }
        }
    }
}

# ---------------------------------------------------------------- 4. Menus and hotkey
Step 'Adding the right-click menus and hotkey'
$setupArgs = @('-P', '-m', 'convert_md', 'setup', '--hotkey', $Hotkey)
if ($NoHotkey) { $setupArgs += '--no-hotkey' }
if ($NoMenus)  { $setupArgs += '--no-menus' }
& $PyExe @PyArgs @setupArgs
if ($LASTEXITCODE -eq 1) { Fail 'Setup failed (see the messages above).' }   # 2 = hotkey skipped

# ---------------------------------------------------------------- 5. Test
if (-not $SkipTest) {
    Step 'Testing conversions'
    $tmp = Join-Path $env:TEMP ('convert-md-test-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    New-Item -ItemType Directory -Path $tmp -ErrorAction Stop | Out-Null
    try {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'samples\Example.md') -Destination $tmp -ErrorAction Stop
        $md = Join-Path $tmp 'Example.md'
        $ok = $false
        & $PyExe @PyArgs -P -m convert_md --to 'docx,xlsx,pptx,html' $md
        $ok = ($LASTEXITCODE -eq 0)
        & $PyExe @PyArgs -P -m convert_md --to md (Join-Path $tmp 'Example.docx')
        $ok = $ok -and ($LASTEXITCODE -eq 0)
        & $PyExe @PyArgs -P -m convert_md --to pdf $md
        if ($LASTEXITCODE -ne 0) {
            Write-Warning 'PDF output is not available. Install Microsoft Word, or run: winget install Typst.Typst'
        }
    } finally {
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (-not $ok) { Fail "A test conversion failed. Details: $env:LOCALAPPDATA\ConvertMd\convert-md.log" }
}

Step 'Checking the installation'
& $PyExe @PyArgs -P -m convert_md doctor

Write-Host "`nDone." -ForegroundColor Green
Write-Host 'Right-click a .md file and choose Show more options > Convert to.'
if (-not $NoHotkey) { Write-Host 'Or select files in File Explorer and press Ctrl+Alt+M.' }
