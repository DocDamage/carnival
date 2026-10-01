"""Sequentially render actual ownership proof actors without editing packages."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/CharacterRepairs/DeanBodyOwnershipBuild_20260930'
for animation in ('MM_Walk_InPlace','MM_Idle'):
 for kind in ('Mixed','Parts'):
  label='DeanOwnership'+kind+('Walk' if 'Walk' in animation else 'Idle')+'_20260930'
  report=ROOT/'Saved/CharacterRepairs'/label/'index.json'
  assert not report.exists(),f'Refuse to replace existing capture evidence: {report}'
  env=os.environ.copy();env.update(CARNIVAL_OUTFIT_INSTANCE=f'/Game/Carnival/Crowd/BodySurfaceProof/Dean{kind}/MHI_Dean{kind}',
   CARNIVAL_OUTFIT_REPORT=label,CARNIVAL_OUTFIT_PROOF_MODES='FullCrowd',
   CARNIVAL_OUTFIT_BODY_ANIMATION=animation,CARNIVAL_OUTFIT_ANIM_TIME='1.0')
  print('Rendering',label,flush=True)
  result=subprocess.run([sys.executable,str(ROOT/'Scripts/run_doll_tool.py'),'render-pie',str(ROOT/'Scripts/review_dean_outfit_isolation_pie.py')],cwd=ROOT,env=env)
  assert result.returncode==0,f'Failed renderer: {label} exit {result.returncode}'
  data=json.loads(report.read_text());assert data['capture_success'] and not data['errors'] and data['engine_exit_code']==0
  print('Captured',label,len(data['captures']),'views; visual review pending',flush=True)
