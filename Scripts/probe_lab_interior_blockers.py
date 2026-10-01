"""Read-only: per sample cell, every surface in the column and the standing-capsule blocker above each walkable one."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CampaignAcceptance/LabInteriorBlockers_20260930';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;NONE=unreal.DrawDebugTrace.NONE
CELLS=[(-43400,-4900),(-43000,-5500),(-42700,-6000),(-42000,-6800),(-41700,-7600),(-42600,-4500)]
R={'success':False,'errors':[],'assets_saved':False,'cells':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def comp(h):return (h[9].get_actor_label() if h[9] else '')+'/'+(h[10].get_name() if h[10] else '')
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 for x,y in CELLS:
  top=2400;hits=[]
  for _ in range(14):
   h=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,top),V(x,y,-1500),TQ,False,[],NONE,True))
   if not h:break
   z=h[5].z;e={'z':round(z,1),'normal_z':round(h[7].z,2),'hit':comp(h)}
   if h[7].z>=.707:
    c=V(x,y,z+98);b=t(unreal.SystemLibrary.capsule_trace_single(world,c,c+V(0,0,.1),42,96,TQ,False,[],NONE,True))
    e['capsule_blocker']=comp(b) if b else None
    if b:e['blocker_impact_z']=round(b[5].z,1)
   hits.append(e);top=z-2
  R['cells'].append({'cell':[x,y],'column':hits})
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
