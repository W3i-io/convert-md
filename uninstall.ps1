<#
.SYNOPSIS
    Removes convert-md's right-click menus and hotkey for the current user.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\uninstall.ps1

.EXAMPLE
    .\uninstall.ps1 -RemovePackage -RemoveData   # also uninstall the Python package, templates and log
#>
[CmdletBinding()]
param(
    [switch]$RemovePackage,   # also pip-uninstall convert-md
    [switch]$RemoveData       # also delete %LOCALAPPDATA%\ConvertMd (templates and log)
)

# Not 'Stop': Windows PowerShell 5.1 can turn harmless messages that pip and Python write to
# stderr into terminating errors. Native commands are checked through $LASTEXITCODE instead.
$ErrorActionPreference = 'Continue'

$PyExe = $null
$PyArgs = @()
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($python -and $python.Source -notlike '*\WindowsApps\*') {
    $PyExe = $python.Source
} elseif (Get-Command py.exe -ErrorAction SilentlyContinue) {
    $PyExe = 'py'; $PyArgs = @('-3')
}

$removed = $false
if ($PyExe) {
    & $PyExe @PyArgs -P -m convert_md remove
    $removed = ($LASTEXITCODE -eq 0)
}

if (-not $removed) {
    Write-Host 'convert-md is not available to Python; removing the menus and hotkey directly.'
    Get-ChildItem 'HKCU:\Software\Classes\SystemFileAssociations' -ErrorAction SilentlyContinue | ForEach-Object {
        foreach ($name in 'ConvertMd', 'ConvertMdToMarkdown', 'MdConvert', 'MdConvertToMarkdown') {
            $key = Join-Path $_.PSPath "shell\$name"
            if (Test-Path -LiteralPath $key) { Remove-Item -LiteralPath $key -Recurse -Force }
        }
    }
    Get-CimInstance Win32_Process -Filter "Name LIKE 'AutoHotkey%'" |
        Where-Object { $_.CommandLine -like '*convert-md-hotkey.ahk*' -or $_.CommandLine -like '*md-convert-hotkey.ahk*' } |
        Invoke-CimMethod -MethodName Terminate | Out-Null
    foreach ($name in 'convert-md-hotkey.lnk', 'md-convert-hotkey.lnk') {
        $lnk = Join-Path ([Environment]::GetFolderPath('Startup')) $name
        if (Test-Path -LiteralPath $lnk) { Remove-Item -LiteralPath $lnk }
    }
    $data = Join-Path $env:LOCALAPPDATA 'ConvertMd'
    foreach ($f in 'convert-md-hotkey.ahk', 'convert-md.ini') {
        $p = Join-Path $data $f
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p }
    }
    Write-Host 'Menus and hotkey removed.'
}

if ($RemovePackage -and $PyExe) {
    & $PyExe @PyArgs -m pip uninstall -y --disable-pip-version-check convert-md
}

if ($RemoveData) {
    $data = Join-Path $env:LOCALAPPDATA 'ConvertMd'
    if (Test-Path -LiteralPath $data) {
        Remove-Item -LiteralPath $data -Recurse -Force
        Write-Host "Deleted $data"
    }
}

Write-Host 'AutoHotkey and Python were left installed. Remove them in Settings > Apps if nothing else uses them.'
