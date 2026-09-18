param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ProjectPath)) {
    throw "Project file not found: $ProjectPath"
}

if ([IO.Path]::GetExtension($ProjectPath) -ne ".uproject") {
    throw "ProjectPath must point to a .uproject file."
}

$ProjectPath = (Resolve-Path $ProjectPath).Path
$ProjectDir = Split-Path $ProjectPath -Parent
$PluginSource = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PluginsDir = Join-Path $ProjectDir "Plugins"
$PluginDest = Join-Path $PluginsDir "CarnivalMetaHumanKit"

New-Item -ItemType Directory -Force -Path $PluginsDir | Out-Null
if ($PluginSource -ne $PluginDest) {
    if (Test-Path $PluginDest) {
        Remove-Item -Recurse -Force $PluginDest
    }
    Copy-Item -Recurse -Force $PluginSource $PluginDest
} else {
    Write-Host "Plugin is already located at: $PluginDest"
}

$uproject = Get-Content $ProjectPath -Raw | ConvertFrom-Json
if ($null -eq $uproject.Plugins) {
    $uproject | Add-Member -NotePropertyName Plugins -NotePropertyValue @()
}

$required = @(
    "CarnivalPopulation",
    "MetaHumanCrowd",
    "MassAI",
    "MassCrowd",
    "StateTree",
    "ZoneGraph",
    "SmartObjects"
)

$plugins = @($uproject.Plugins)
foreach ($name in $required) {
    $existing = $plugins | Where-Object { $_.Name -eq $name } | Select-Object -First 1
    if ($null -eq $existing) {
        $plugins += [PSCustomObject]@{ Name = $name; Enabled = $true }
    } else {
        $existing.Enabled = $true
    }
}
$uproject.Plugins = $plugins

$uproject | ConvertTo-Json -Depth 100 | Set-Content $ProjectPath -Encoding UTF8

Write-Host "Installed CarnivalMetaHumanKit to: $PluginDest"
Write-Host "Enabled CarnivalPopulation + MetaHuman/Mass crowd dependencies in the .uproject."
Write-Host "Next: regenerate project files/build, then open Unreal Engine 5.8."
