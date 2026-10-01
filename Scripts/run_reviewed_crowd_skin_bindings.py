"""Save and fresh-reload one reviewed head collection at a time; stop on failures."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBindings_20260930'
REPORT={'success':False,'groups':[],'errors':[],'started':time.time()}
def save():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'Batch.json').write_text(json.dumps(REPORT,indent=2))
save()
try:
    for group in ['G'+str(i) for i in range(1,7)]:
        env=os.environ.copy();env['CARNIVAL_BIND_GROUP']=group
        row={'group':group,'success':False};REPORT['groups'].append(row);save()
        for step,script in [('Save','bind_reviewed_crowd_head_skins.py'),('Reload','verify_crowd_head_skin_bindings.py')]:
            env['CARNIVAL_EDITOR_SCRIPT']=str(ROOT/'Scripts'/script);started=time.time()
            result=subprocess.run([sys.executable,str(ROOT/'Scripts/run_doll_tool.py'),
                'editor' if step=='Save' else 'unreal',
                str(ROOT/'Scripts/run_editor_authoring_guarded.py') if step=='Save' else str(ROOT/'Scripts'/script)],
                cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            directory=OUT/group;directory.mkdir(parents=True,exist_ok=True)
            (directory/(step+'_console.log')).write_text(result.stdout)
            log=ROOT/'Saved/HauntedDollIntegration'/('run_editor_authoring_guarded_engine.log' if step=='Save' else 'verify_crowd_head_skin_bindings_engine.log')
            if log.exists():shutil.copy2(log,directory/(step+'_engine.log'))
            row[step]={'exit':result.returncode,'elapsed':time.time()-started};save()
            assert result.returncode==0,(group,step,result.stdout[-2000:])
            evidence=json.loads((directory/('index.json' if step=='Save' else 'Reload.json')).read_text())
            assert evidence['success'] and not evidence['errors'],(group,step,evidence['errors'])
        row['success']=True;save();print(group,'bound, saved and fresh-reloaded',flush=True)
    REPORT['success']=True
except Exception as error:
    REPORT['errors'].append(str(error));raise
finally:save()
