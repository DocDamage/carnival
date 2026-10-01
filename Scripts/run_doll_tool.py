"""Run the installed Unreal/Blender tools with explicit argument lists and logs."""
import subprocess
import sys
import json
import time
import os
import shutil
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
    "all-test-audio": ("Carnival", "FullAutomationAudio", "Full_Test_Audio.log"),
}
if mode == "blender":
    args = [r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe", "--background", "--factory-startup", "--python-exit-code", "1", "--python", str(script)]
elif mode == "unreal":
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "-unattended", "-nullrhi", "-nosplash", "-nop4", "-NoSound",
            "-run=pythonscript", "-script=" + str(script), "-abslog=" + str(logs / (script.stem + "_engine.log"))]
elif mode in ("build", "game-build"):
    dotnet = sorted((engine / "Binaries/ThirdParty/DotNet").glob("**/win-x64/dotnet.exe"))[-1]
    args = [str(dotnet), str(engine / "Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll"),
            "CarnivalGameEditor" if mode == "build" else "CarnivalGame", "Win64", "Development", "-Project=" + str(base / "CarnivalGame.uproject"),
            "-WaitMutex", "-NoHotReloadFromIDE", "-MaxParallelActions=6"]
elif mode in test_modes:
    test_filter, report_folder, engine_log = test_modes[mode]
    args = [str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-nullrhi", "-nosplash", "-nop4", "-NoSound",
            "-ExecCmds=Automation RunTests " + test_filter, "-TestExit=Automation Test Queue Empty",
            "-ReportExportPath=" + str(logs / report_folder),
            "-abslog=" + str(logs / engine_log)]
    if mode == 'all-test-audio':
        args.remove('-NoSound')
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
elif mode == "render-pie":
    render_rhi=os.environ.get('CARNIVAL_RENDER_RHI','dx12')
    assert render_rhi in ('dx11','dx12'),render_rhi
    args = [str(engine / "Binaries/Win64/UnrealEditor.exe"), str(base / "CarnivalGame.uproject"),
            "/Engine/Maps/Entry", "-unattended", "-RenderOffscreen", "-"+render_rhi, "-nosplash", "-nop4", "-NoSound",
            "-windowed", "-ResX=1280", "-ResY=800", "-ExecutePythonScript=" + str(script),
            "-abslog=" + str(logs / (script.stem + "_engine.log"))]
else:
    raise ValueError(mode)
log = logs / ((script.stem if script else mode) + "_console.log")
child_env = os.environ.copy()
# Installed TargetPlatformManagerModule.cpp supports this for local editor
# sessions. Native builds retain normal SDK validation; no global env changes.
if mode in ("unreal", "render", "editor", "playtest", "render-pie") or mode in test_modes:
    child_env["UE_SKIP_UBT_SDK_SETUP"] = "1"
native_dump_dir = child_env.get('CARNIVAL_NATIVE_DUMP_DIR')
if native_dump_dir:
    assert mode in ('editor', 'render-pie', 'playtest'), 'Native observer is scoped to diagnostic editor runs'
    observer = base/'Saved/Diagnostics/NativeCrashObserver.exe'
    assert observer.exists(), 'Build Scripts/build_native_crash_observer.cmd first'
    dump_dir = Path(native_dump_dir).resolve()
    assert dump_dir.is_relative_to(base/'Saved/CharacterRepairs'), 'Keep native diagnostics in the project report folder'
    args = [str(observer), str(dump_dir), *args]
with log.open("w", encoding="utf-8") as output:
    started_at = time.time()
    result = subprocess.run(args, cwd=base, env=child_env, stdout=output, stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NO_WINDOW)
print(mode, "exit", result.returncode, "log", log, flush=True)
print(log.read_text(errors="replace")[-1500:])
if script and script.stem == 'run_editor_authoring_guarded' and result.returncode == 0:
    target=Path(child_env['CARNIVAL_EDITOR_SCRIPT']).stem
    guard_path=logs/(target+'_guard.json')
    if not guard_path.exists() or guard_path.stat().st_mtime < started_at or not json.loads(guard_path.read_text()).get('success'):
        print('Editor authoring did not produce a fresh successful guard report:',guard_path)
        sys.exit(1)
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
    if script.stem == 'playtest_world_expansion_walk_routes' and child_env.get('CARNIVAL_EXPANSION_REPORT'):
        route_reports[script.stem] = ('WorldExpansion', child_env['CARNIVAL_EXPANSION_REPORT'] + '.json')
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
if mode in ('playtest','render-pie') and script:
    acceptance_reports = {
        'verify_crowd_roaming_pie': base/'Saved/CrowdAcceptance'/child_env.get('CARNIVAL_CROWD_REPORT','RoamingPIE_20260930')/'index.json',
        'playtest_all_attended_rides': base/'Saved/RideDevelopment'/child_env.get('CARNIVAL_RIDE_REPORT','AllRidePIE_'+child_env['CARNIVAL_RIDE_LIGHTING'] if child_env.get('CARNIVAL_RIDE_LIGHTING') else 'AllRidePIE')/'index.json',
        'inspect_ride_seats_pie': base/'Saved/RideDevelopment/ConstructedSeatIds.json',
        'playtest_bumper_arena': base/'Saved/RideDevelopment/BumperArenaPIE/index.json',
        'playtest_interior_camera_roundtrips': base/'Saved/WorldExpansion/InteriorCameraAcceptance'/(child_env.get('CARNIVAL_INTERIOR_REPORT','Roundtrips')+'.json'),
        'review_settings_readability_pie': base/'Saved/PresentationAcceptance/SettingsReadability/index.json',
        'review_session_menu_pie': base/'Saved/PresentationAcceptance/SessionMenu/index.json',
        'review_populated_carnival_pie': base/'Saved/PresentationAcceptance'/child_env.get('CARNIVAL_POPULATED_REPORT','PopulatedCarnival')/'index.json',
        'compare_midway_night_fill_pie': base/'Saved/PresentationAcceptance'/child_env.get('CARNIVAL_NIGHT_FILL_REPORT','NightFillComparison_20260930')/'index.json',
        'review_dean_skin_bake_pie': base/'Saved/CharacterRepairs/DeanSkinRenderedProof_20260930/index.json',
        'review_dean_outfit_isolation_pie': base/'Saved/CharacterRepairs'/child_env.get('CARNIVAL_OUTFIT_REPORT','DeanOutfitIsolation_20260930')/'index.json',
        'review_g1_clothing_family_pie': base/'Saved/CharacterRepairs'/child_env.get('CARNIVAL_FAMILY_GALLERY_REPORT','G1ClothingFamilyGallery_20260930')/'index.json',
        'review_dean_family_pose_pie': base/'Saved/CharacterRepairs/DeanFamilyPoseAndShadow_20260930/index.json',
        'review_dean_retarget_policy_pie': base/'Saved/CharacterRepairs/DeanRetargetPolicyAndBodyShadow_20260930/index.json',
        'review_dean_authored_reference_pie': base/'Saved/CharacterRepairs/DeanAuthoredReferenceAndGarmentShadow_20260930/index.json',
        'review_dean_space_conversion_pie': base/'Saved/CharacterRepairs/DeanAnimationSpaceConversionSampled_20260930/index.json',
        'review_crowd_head_skin_candidates_pie': base/'Saved/CharacterRepairs'/child_env.get('CARNIVAL_SKIN_CANDIDATE_REPORT','CrowdHeadSkinCandidates_20260930')/'index.json',
        'review_dean_integrated_crowd_pie': base/'Saved/CharacterRepairs'/child_env.get('CARNIVAL_DEAN_LIVE_REPORT','DeanCrowdLiveAcceptance_20260930')/'index.json',
        'survey_water_vehicle_placements': base/'Saved/WorldExpansion/WaterVehicleAcceptance'/(child_env.get('CARNIVAL_VEHICLE_WORLD','main')+'_PlacementSurvey.json'),
        'review_lab_b_gallery_pie': base/'Saved/WorldExpansion/LabB_Gallery_PIE/Review.json',
        'playtest_balloon_station_walks': base/'Saved/RideDevelopment'/(child_env.get('CARNIVAL_BALLOON_WALK_REPORT','Balloon_Station_Walks')+'.json'),
        'survey_dock_water_depth': base/'Saved/WorldExpansion/WaterVehicleAcceptance'/('DockWaterBerth.json' if child_env.get('CARNIVAL_WATER_DEPTH_AREA') == 'boat_berth' else 'DockWaterDepth.json'),
        'playtest_integrated_water_vehicle_lifecycle': base/'Saved/WorldExpansion/WaterVehicleAcceptance'/(child_env.get('CARNIVAL_VEHICLE_LABEL','Hovercraft_NorthDock_Handling')+'_Lifecycle.json'),
        'review_child_roster_pie': base/'Saved/CharacterAcceptance/ChildPreview'/(('FaceCloseups'+child_env.get('CARNIVAL_CHILD_PREVIEW_VARIANT','')+'/index.json') if child_env.get('CARNIVAL_CHILD_FACE_PREVIEW')=='1' else 'BlackBoyConsistentBind/index.json' if child_env.get('CARNIVAL_CHILD_CONSISTENT_BIND')=='1' else 'BlackBoyReferenceAlignment/index.json' if child_env.get('CARNIVAL_CHILD_REFERENCE_COMPARISON')=='1' else 'index.json'),
    }
    report_path = acceptance_reports.get(script.stem)
    if report_path:
        if not report_path.exists() or report_path.stat().st_mtime < started_at:
            print('No fresh acceptance report:', report_path)
            if result.returncode==0:sys.exit(1)
            report_path.parent.mkdir(parents=True,exist_ok=True)
            report={'success':False,'errors':['Engine exited before a fresh acceptance report'],
                    'limits':'Failure diagnostics only; no capture, gameplay or performance acceptance.'}
        else:report=json.loads(report_path.read_text(encoding='utf-8-sig'))
        report['engine_exit_code']=result.returncode
        if mode=='render-pie':report['render_rhi']=render_rhi
        if script.stem in ('review_populated_carnival_pie','verify_crowd_roaming_pie','compare_midway_night_fill_pie','review_dean_integrated_crowd_pie','review_crowd_head_skin_candidates_pie'):
            engine_log=logs/(script.stem+'_engine.log')
            if engine_log.exists():
                engine_text=engine_log.read_text(errors='replace')
                representation_errors=engine_text.count('LogMassRepresentation: Error:')
                report['representation_error_count']=representation_errors
                if representation_errors:
                    report['success']=False
                    report.setdefault('errors',[]).append(str(representation_errors)+' live Mass representation errors; see engine log')
                for key,pattern,label in (
                    ('blueprint_runtime_error_count', 'PIE: Error: Blueprint Runtime Error:', 'Blueprint runtime errors'),
                    ('crowd_spawn_error_count', 'LogCarnivalCrowdSpawn: Error:', 'crowd spawn errors'),
                    ('metahuman_representation_error_count', 'LogMetaHumanMassRepresentation: Error:', 'MetaHuman representation errors')):
                    count=engine_text.count(pattern)
                    report[key]=count
                    if count:
                        report['success']=False
                        report.setdefault('errors',[]).append(str(count)+' '+label+'; see engine log')
        if result.returncode != 0:
            report['success']=False
            report.setdefault('errors',[]).append('Engine process exited with code '+str(result.returncode))
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        # Preserve per-case engine diagnostics before the next lighting/route
        # run reuses this script's central log filenames.
        for source,suffix in ((logs/(script.stem+'_engine.log'),'_engine.log'),
                              (log,'_console.log')):
            if source.exists():
                shutil.copy2(source,report_path.with_name(report_path.stem+suffix))
        print('Acceptance:', {'success':report.get('success'),'errors':report.get('errors',[])})
        if not report.get('success') or report.get('errors'):
            sys.exit(1)
sys.exit(result.returncode)
