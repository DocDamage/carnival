"""Run exactly one child's disposable source project with fresh-result checking."""
import json,os,subprocess,sys,time
from pathlib import Path
import psutil

ROOT=Path(__file__).resolve().parents[1]
identity=sys.argv[1]
workspace=next(row for row in json.loads((ROOT/'Saved/CharacterAcceptance/ChildSources/MigrationWorkspaces.json').read_text())['workspaces'] if row['identity']==identity)
for process in psutil.process_iter(['name']):
    if process.info['name'] in ('UnrealEditor.exe','UnrealEditor-Cmd.exe'):
        raise RuntimeError('Another Unreal process is active; keep source migration sequential')
out=ROOT/'Saved/CharacterAcceptance/ChildSources'
env=os.environ.copy();env.update(CARNIVAL_CHILD_SOURCE=identity,UE_SKIP_UBT_SDK_SETUP='1')
args=[r'C:\Program Files\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe',workspace['project'],
    '/Engine/Maps/Entry','-unattended','-nullrhi','-nosplash','-nop4','-NoSound',
    '-run=pythonscript','-script='+str(ROOT/'Scripts/migrate_child_source_project.py'),
    '-abslog='+str(out/(identity+'_Migration_engine.log'))]
started=time.time()
with (out/(identity+'_Migration_console.log')).open('w',encoding='utf-8') as stream:
    result=subprocess.run(args,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW)
report_path=out/(identity+'_Migration.json')
report=json.loads(report_path.read_text()) if report_path.exists() and report_path.stat().st_mtime>=started else {}
if report:
    report['engine_exit_code']=result.returncode
    report['transfer_complete']=bool(report.get('success'))
    if result.returncode:
        report['success']=False
        report.setdefault('errors',[]).append('Engine process exited '+str(result.returncode)+'; inspect its preserved engine log')
    report_path.write_text(json.dumps(report,indent=2))
print(json.dumps({'exit':result.returncode,'success':report.get('success'),
    'assets':len(report.get('assets',[])),'errors':report.get('errors',[])},indent=2))
sys.exit(0 if result.returncode==0 and report.get('success') else 1)
