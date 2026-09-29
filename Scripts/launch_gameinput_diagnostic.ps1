param([switch]$Launch)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskOutput = Join-Path $taskRoot 'Saved\InputDiagnostics'
New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
$taskEngine = 'C:\Program Files\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$taskArguments = @(
    (Join-Path $taskRoot 'CarnivalGame.uproject'),
    '/Engine/Maps/Entry',
    '-nullrhi', '-nosound', '-unattended', '-nosplash',
    '-EnablePlugins=GameInputWindows',
    '-ini:Input:[GameInputPlatformSettings_Windows GameInputPlatformSettings]:bProcessGamepad=True,bProcessController=True,bProcessRawInput=True,bSpecialDevicesRequireExplicitDeviceConfiguration=True',
    '-LogCmds=LogGameInput VeryVerbose',
    ('-ExecutePythonScript=' + (Join-Path $PSScriptRoot 'inspect_gameinput_process.py')),
    ('-abslog=' + (Join-Path $taskOutput 'GameInput_Enumeration.log'))
)
$taskManifest = [ordered]@{
    executable=$taskEngine
    arguments=$taskArguments
    configurationSaved=$false
    purpose='Process-only device-kind/VID/PID enumeration; no guessed device mappings'
    sourceEvidence=@(
        'PluginManager.cpp: EnablePlugins= command-line support',
        'GameInputDeveloperSettings.h: Input config / UPlatformSettings per-object settings',
        'PlatformSettingsManager.cpp: GameInputPlatformSettings_Windows transient instance',
        'Obj.cpp HandlePerObject: section = instance-name plus class-name',
        'GameInputDeviceContainer.cpp: explicit config gate prevents unconfigured Controller/Raw processing'
    )
}
$taskManifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskOutput 'GameInput_Launch.json') -Encoding utf8
if ($Launch) {
    # Start-Process joins arguments; quote each complete argument to preserve the
    # spaces in engine/project paths and the per-object configuration section.
    $taskQuotedArguments = $taskArguments | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }
    $taskProcess = Start-Process -FilePath $taskEngine -ArgumentList $taskQuotedArguments -WindowStyle Hidden -PassThru
    [pscustomobject]@{ ProcessId=$taskProcess.Id; Log=(Join-Path $taskOutput 'GameInput_Enumeration.log') }
} else {
    $taskManifest | ConvertTo-Json -Depth 6
}
