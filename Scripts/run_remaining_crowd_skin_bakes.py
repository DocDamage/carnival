"""Run bounded, sequential stock bakes and separate reloads; stop on any failure."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBakes_20260930'
NAMES=['MHC_Advika','Petra','MHC_Hannah','MHC_Kabir','Mason','MHC_Crowd84','MHC_Seo','Skye',
       'AmandaBlack','MHC_Natasha','Skotukeda3','Skotukeda4','MHC_Base_Female']
REPORT={'success':False,'heads':[],'errors':[],'started':time.time()}
def save():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'Batch.json').write_text(json.dumps(REPORT,indent=2))
save()
try:
    for name in NAMES:
        env=os.environ.copy();env['CARNIVAL_HEAD_NAME']=name
        row={'head':name,'success':False};REPORT['heads'].append(row);save()
        for step,script in [('Save','bake_crowd_head_skin.py'),('Reload','verify_crowd_head_skin.py')]:
            env['CARNIVAL_EDITOR_SCRIPT']=str(ROOT/'Scripts'/script)
            started=time.time()
            result=subprocess.run([sys.executable,str(ROOT/'Scripts/run_doll_tool.py'),'editor',
                str(ROOT/'Scripts/run_editor_authoring_guarded.py')],cwd=ROOT,env=env,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            directory=OUT/name;directory.mkdir(parents=True,exist_ok=True)
            (directory/(step+'_console.log')).write_text(result.stdout)
            log=ROOT/'Saved/HauntedDollIntegration/run_editor_authoring_guarded_engine.log'
            if log.exists():shutil.copy2(log,directory/(step+'_engine.log'))
            row[step]={'exit':result.returncode,'elapsed':time.time()-started};save()
            assert result.returncode==0,(name,step,result.stdout[-2000:])
            evidence=json.loads((directory/('index.json' if step=='Save' else 'Reload.json')).read_text())
            assert evidence['success'] and not evidence['errors'],(name,step,evidence['errors'])
        row['success']=True;save();print(name,'saved and fresh-reloaded',flush=True)
    REPORT['success']=True
except Exception as error:
    REPORT['errors'].append(str(error));raise
finally:save()
