"""Read-only: run the finder's floor/standing/edge checks along the PIE-walked Lab A path."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
src=(ROOT/'Scripts/find_campaign_station_sites.py').read_text()
src=src[:src.index('\ntry:\n before=')].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(src,'finder_defs','exec'),g)
V=unreal.Vector
walk=json.loads((ROOT/'Saved/CampaignAcceptance/LabGateWalk3_20260930/index.json').read_text())['samples']
R={'success':False,'errors':[],'points':[]}
try:
 g['world']=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 g['WALK_IGNORE'].extend(a for a in acts if a.get_actor_label().startswith('BP_MGate01'))
 pts=[s['loc'] for s in walk]
 prev=None
 for x,y,z in pts:
  for k in range(4):
   if prev is None:px,py,pz=x,y,z
   else:px,py,pz=[prev[i]+(c-prev[i])*(k+1)/4 for i,c in enumerate((x,y,z))]
   f=g['floor_at'](px,py,pz+60,pz-250)
   row={'p':[round(px),round(py)],'floor':round(f.z,1) if f else None}
   if f:
    c=f+V(0,0,98);h=g['capsule_hit'](c,c+V(1,0,0));row['standing_blocker']=g['name'](h) if h else None
    if prev is not None and 'last' in R:row['edge_ok_from_prev']=g['edge_ok'](R['last'],c)
    R['last']=c
   else:
    h=g['t'](unreal.SystemLibrary.line_trace_single(g['world'],V(px,py,pz+60),V(px,py,pz-250),g['TQ'],False,g['WALK_IGNORE'],g['NONE'],True))
    row['raw_hit']=[round(h[5].z,1),round(h[7].z,2),g['name'](h)] if h else None
   R['points'].append(row)
   if prev is None:break
  prev=(x,y,z)
 R.pop('last',None);R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:
 R.pop('last',None);(ROOT/'Saved/CampaignAcceptance/LabWalkPathChecks_20260930.json').write_text(json.dumps(R,indent=1,default=str))
