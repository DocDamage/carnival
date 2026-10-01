"""Read-only: floor-height map (50 cm grid) of the Lab A/B area at entry level; standing clearance per cell."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CampaignAcceptance/LabFloorMapAfterRotationFix_20260930';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;NONE=unreal.DrawDebugTrace.NONE
R={'success':False,'errors':[],'assets_saved':False}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 X0,X1,Y0,Y1,S=-44300,-40300,-8500,-4300,50
 rows=[];actors={}
 for y in range(Y1,Y0-1,-S):
  row=[]
  for x in range(X0,X1+1,S):
   # Every surface in the column, top to bottom; keep standing-clear walkable floors.
   top=2400;cell=[]
   for _ in range(12):
    h=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,top),V(x,y,-1200),TQ,False,[],NONE,True))
    if not h:break
    z=h[5].z;a=h[9].get_actor_label() if h[9] else ''
    if h[7].z>=.707:
     c=V(x,y,z+98)
     if not t(unreal.SystemLibrary.capsule_trace_single(world,c,c+V(0,0,.1),42,96,TQ,False,[],NONE,True)):
      cell.append([round(z),a]);actors[a]=actors.get(a,0)+1
    top=z-40
   row.append(cell)
  rows.append(row)
 gate=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label().startswith('BP_MGate01')]
 R['gate']=[{'label':g.get_actor_label(),'class':g.get_class().get_name(),'components':[{'name':c.get_name(),'class':c.get_class().get_name(),
   'collision':str(c.get_collision_enabled()) if hasattr(c,'get_collision_enabled') else None,
   'loc':list(c.get_world_location().to_tuple()) if hasattr(c,'get_world_location') else None,
   'mesh':c.static_mesh.get_name() if hasattr(c,'static_mesh') and c.static_mesh else None} for c in g.get_components_by_class(unreal.SceneComponent)]} for g in gate]
 R.update(grid={'x0':X0,'x1':X1,'y0':Y0,'y1':Y1,'step':S},rows=rows,floor_actors=sorted(actors.items(),key=lambda kv:-kv[1])[:40],success=True)
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R))
