"""Run the installed Unreal/Blender tools with explicit argument lists and logs."""
import subprocess
import sys
import json
import time
import os
from pathlib import Path

base = Path(r"F:\Carnival")
logs = base / "Saved/HauntedDollIntegration"
logs.mkdir(parents=True, exist_ok=True)
mode = sys.argv[1]
script = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
engine = Path(r"C:\Program Files\UE_5.8\Engine")
test_modes = {
    "test": ("Carnival.HauntedDoll", "Automation", "Encounter_Test.log"),
    "ride-test": ("Carnival.Rides", "RideAutomation", "Ride_Test.log"),
    "motorcycle-test": ("Carnival.Motorcycle", "MotorcycleAutomation", "Motorcycle_Test.log"),
    "all-test": ("Carnival", "FullAutomation", "Full_Test.log"),
}
if mode == "blender":
    args = [r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe", "--background", "--factory-startup", "--python-exit-code", "1", "--python", str(script)]
elif mode == "unreal":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "-unattended", "-nullrhi", "-nosplash", "-nop4", "-NoSound",
            "-run=pythonscript", "-script=" + str(script), "-abslog=" + str(logs / (script.stem + "_engine.log"))]
elif mode == "build":
    dotnet = sorted((engine / "Binaries/ThirdParty/DotNet").glob("**/win-x64/dotnet.exe"))[-1]
    args = [str(dotnet), str(engine / "Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll"),
            "CarnivalGameEditor", "Win64", "Development", "-Project=" + str(base / "CarnivalGame.uproject"),
            "-WaitMutex", "-NoHotReloadFromIDE", "-MaxParallelActions=6"]
elif mode in test_modes:
    test_filter, report_folder, engine_log = test_modes[mode]
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-nullrhi", "-nosplash", "-nop4", "-NoSound",
            "-ExecCmds=Automation RunTests " + test_filter, "-TestExit=Automation Test Queue Empty",
            "-ReportExportPath=" + str(logs / report_folder),
            "-abslog=" + str(logs / engine_log)]
elif mode == "render":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-RenderOffscreen", "-nosplash", "-nop4", "-NoSound",
            "-AllowCommandletRendering", "-run=pythonscript", "-script=" + str(script),
            "-abslog=" + str(logs / (script.stem + "_engine.log"))]
elif mode == "editor":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-RenderOffscreen", "-nosplash", "-nop4", "-NoSound",
            "-ExecCmds=py " + str(script), "-abslog=" + str(logs / (script.stem + "_engine.log"))]
elif mode == "playtest":
    # PIE route callbacks need the persistent Slate loop in UnrealEditor.exe.
    # UnrealEditor-Cmd.exe exits after ExecCmds and truncates live traversal to
    # one or two callbacks, which is not route evidence.
    args = [str(engine / "Binaries/Win64/UnrealEditor.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-nullrhi", "-nosplash", "-nop4", "-NoSound",
            "-ExecCmds=py " + str(script), "-abslog=" + str(logs / (script.stem + "_engine.log"))]
else:
    raise ValueError(mode)
log = logs / ((script.stem if script else mode) + "_console.log")
child_env = os.environ.copy()
# Installed TargetPlatformManagerModule.cpp supports this for local editor
# sessions. Native builds retain normal SDK validation; no global env changes.
if mode in ("unreal", "render", "editor", "playtest") or mode in test_modes:
    child_env["UE_SKIP_UBT_SDK_SETUP"] = "1"
with log.open("w", encoding="utf-8") as output:
    started_at = time.time()
    result = subprocess.run(args, cwd=base, env=child_env, stdout=output, stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NO_WINDOW)
print(mode, "exit", result.returncode, "log", log, flush=True)
print(log.read_text(errors="replace")[-1500:])
if mode in test_modes and result.returncode == 0:
    report_path = logs / test_modes[mode][1] / "index.json"
    if not report_path.exists() or report_path.stat().st_mtime < started_at:
        print("Automation failed to produce a fresh report")
        sys.exit(1)
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    print("Automation:", {key: report.get(key) for key in ("succeeded", "succeededWithWarnings", "failed", "notRun", "inProcess")})
    if report.get("failed", 0) or report.get("notRun", 0) or report.get("inProcess", 0) or not report.get("tests") or any(test.get("state") != "Success" for test in report.get("tests", [])):
        sys.exit(1)
if mode == 'playtest' and result.returncode == 0:
    route_reports = {
        'playtest_hospital_motorcycle_route': ('IndustrialHospital', 'Motorcycle_Route_Playtest.json'),
        'probe_motorcycle_route_stall': ('IndustrialHospital', 'Motorcycle_Tyre_Stall_Probe.json'),
        'playtest_industrial_hospital_route': ('IndustrialHospital', 'Route_Playtest.json'),
        'playtest_world_expansion_walk_routes': ('WorldExpansion', 'Walk_Route_Playtest.json'),
    }
    custom_route_report = child_env.get('CARNIVAL_ROUTE_REPORT_PREFIX')
    if custom_route_report and script.stem == 'playtest_industrial_hospital_route':
        route_reports[script.stem] = ('IndustrialHospital', custom_route_report + '.json')
    if script.stem in route_reports:
        report_folder, report_file = route_reports[script.stem]
        report_path = base / 'Saved' / report_folder / report_file
        if not report_path.exists() or report_path.stat().st_mtime < started_at:
            print('Route playtest failed to produce a fresh report')
            sys.exit(1)
        report = json.loads(report_path.read_text(encoding='utf-8-sig'))
        print('Route:', {'success': report.get('success'), 'errors': report.get('errors', [])})
        if not report.get('success') or report.get('errors') or not report.get('tests') or any(not test.get('success') for test in report['tests']):
            sys.exit(1)
sys.exit(result.returncode)
