"""Force a fresh Windows cook/archive only after the saved outer route passes PIE."""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT=Path(r'F:\Carnival')
OUT=ROOT/'Saved/WorldExpansion'
region=OUT/'Region_Authoring.json'
play=json.loads((OUT/'Outer_Final_Route_PIE.json').read_text())
if not play.get('success') or play.get('errors'):
    raise RuntimeError('Fresh route PIE has not passed; package refresh is gated')
if play['region_authoring_sha256'] != hashlib.sha256(region.read_bytes()).hexdigest():
    raise RuntimeError('The route changed after the passing PIE run')
outer=[t for t in play['tests'] if t['name'].startswith('outer_surface')]
if len(outer)!=2 or not all(t['success'] for t in outer):
    raise RuntimeError('Both continuous outer-route directions are required')
audit=json.loads((OUT/'Route_Collision_Audit.json').read_text())['routes'][0]
if not audit['static_trace_clear'] or not audit['authored_surface_capsule_clear']:
    raise RuntimeError('Outer-route static clearance has not passed')
if shutil.disk_usage(ROOT).free < 70*1024**3:
    raise RuntimeError('At least 70 GiB free is required for the separate fresh cook/stage/archive')
engine=Path(r'C:\Program Files\UE_5.8\Engine')
dotnet=sorted((engine/'Binaries/ThirdParty/DotNet').glob('**/win-x64/dotnet.exe'))[-1]
name='WindowsDev_20260929_RouteRefresh'
archive=ROOT/'Saved/Packages'/name
stage=ROOT/'Saved/Packages'/(name+'_Stage')
log=ROOT/'Saved/Packages'/(name+'_UAT.log')
env=os.environ.copy()
env['UE-LocalDataCachePath']=str(ROOT/'DerivedDataCache')
# Reuse the prior cook's cache without writing to the nearly full system drive.
ddc='(ProjectPak,InstalledProjectPak,EnginePak=InstalledEnginePak,Local=InstalledLocal,Previous=(Type=FileSystem,Path=C:/Users/dferr/AppData/Local/UnrealEngine/Common/DerivedDataCache,ReadOnly=true,DeleteUnused=false,Touch=false))'
args=[str(dotnet),str(engine/'Binaries/DotNET/AutomationTool/AutomationTool.dll'),'BuildCookRun',
      '-project='+str(ROOT/'CarnivalGame.uproject'),'-noP4','-platform=Win64','-clientconfig=Development',
      '-skipbuild','-cook','-stage','-pak','-iostore','-archive','-archivedirectory='+str(archive),
      '-stagingdirectory='+str(stage),'-prereqs','-utf8output','-nocompileuat','-forcerecook',
      '-AdditionalCookerOptions=-skipzenstore -ddc='+ddc+' -LocalDataCachePath='+str(ROOT/'DerivedDataCache')+' -ini:Engine:[DevOptions.Shaders]:NumUnusedShaderCompilingThreads=26 -ini:Engine:[DevOptions.Shaders]:NumUnusedShaderCompilingThreadsDuringGame=26']
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'route_sha256':play['region_authoring_sha256'],
        'archive':str(archive),'stage':str(stage),'log':str(log),'command':args,'success':False,
        'build_basis':'Native code unchanged in this continuation; reuses the previously successful UE 5.8.3 Development build. Content is force-recooked.'}
destination=OUT/'Route_Refresh_Package.json'
destination.write_text(json.dumps(report,indent=2))
with log.open('w',encoding='utf-8') as output:
    result=subprocess.run(args,env=env,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
report.update(exit_code=result.returncode,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
launch_directory = archive if (archive/'CarnivalGame.exe').exists() else archive/'Windows'
report['launch_directory'] = str(launch_directory)
report['success']=result.returncode==0 and (launch_directory/'CarnivalGame.exe').exists()
destination.write_text(json.dumps(report,indent=2))
print(json.dumps({k:report[k] for k in ('success','exit_code','archive','log')}))
raise SystemExit(0 if report['success'] else 1)
