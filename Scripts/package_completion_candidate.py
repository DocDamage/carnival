"""Build and fresh-cook a separate diagnostic candidate; never reuse old cooked data."""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'Saved/WorldExpansion'
ENGINE = Path(r'C:\Program Files\UE_5.8\Engine')
if shutil.disk_usage(ROOT).free < 70*1024**3:
    raise RuntimeError('Fresh cook/stage/archive requires at least 70 GiB free')
tests_path = max((p for p in (ROOT/'Saved/HauntedDollIntegration/FullAutomation/index.json',
                             ROOT/'Saved/HauntedDollIntegration/FullAutomationAudio/index.json') if p.exists()),
                 key=lambda p:p.stat().st_mtime)
tests = json.loads(tests_path.read_text(encoding='utf-8-sig'))
if not tests.get('succeeded') or any(t.get('state') != 'Success' for t in tests.get('tests', [])):
    raise RuntimeError('Native Carnival automation must pass before candidate packaging')
name = 'CompletionCandidate_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
archive = ROOT/'Saved/Packages'/name
stage = ROOT/'Saved/Packages'/(name+'_Stage')
log = ROOT/'Saved/Packages'/(name+'_UAT.log')
assert not archive.exists() and not stage.exists()
dotnet = sorted((ENGINE/'Binaries/ThirdParty/DotNet').glob('**/win-x64/dotnet.exe'))[-1]
env = os.environ.copy()
env['UE-LocalDataCachePath'] = str(ROOT/'DerivedDataCache')
ddc = '(ProjectPak,InstalledProjectPak,EnginePak=InstalledEnginePak,Local=InstalledLocal,Previous=(Type=FileSystem,Path=C:/Users/dferr/AppData/Local/UnrealEngine/Common/DerivedDataCache,ReadOnly=true,DeleteUnused=false,Touch=false))'
args = [str(dotnet), str(ENGINE/'Binaries/DotNET/AutomationTool/AutomationTool.dll'), 'BuildCookRun',
        '-project='+str(ROOT/'CarnivalGame.uproject'), '-noP4', '-platform=Win64', '-clientconfig=Development',
        '-build', '-cook', '-stage', '-pak', '-iostore', '-archive', '-archivedirectory='+str(archive),
        '-stagingdirectory='+str(stage), '-prereqs', '-utf8output', '-nocompileuat', '-forcerecook',
        '-AdditionalCookerOptions=-skipzenstore -ddc='+ddc+' -LocalDataCachePath='+str(ROOT/'DerivedDataCache')+
        ' -ini:Engine:[DevOptions.Shaders]:NumUnusedShaderCompilingThreads=26'+
        ' -ini:Engine:[DevOptions.Shaders]:NumUnusedShaderCompilingThreadsDuringGame=26']
report = {'success': False, 'scope': 'Fresh native/content diagnostic candidate, not full-game acceptance.',
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'automation_sha256': hashlib.sha256(tests_path.read_bytes()).hexdigest(),
          'automation_pass_count': tests['succeeded'], 'archive': str(archive), 'stage': str(stage),
          'log': str(log), 'command': args}
destination = OUT/'Completion_Candidate_Package.json'
destination.write_text(json.dumps(report, indent=2))
with log.open('w', encoding='utf-8') as output:
    result = subprocess.run(args, env=env, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NO_WINDOW)
launch = archive if (archive/'CarnivalGame.exe').exists() else archive/'Windows'
report.update(exit_code=result.returncode, launch_directory=str(launch),
              finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              success=result.returncode == 0 and (launch/'CarnivalGame.exe').exists())
destination.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['success'] else 1)
