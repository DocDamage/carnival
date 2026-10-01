"""Read-only: prison wall-art facing, the tower interior floor, and sight from art front points."""
import json,math
from pathlib import Path
import unreal
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
out=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 l=a.get_actor_label()
 if not l.startswith('WorldExpansion_WallArt_Prison'):continue
 c=a.get_actor_location();f=a.get_actor_forward_vector();r=a.get_actor_right_vector()
 row={'label':l,'loc':[round(v) for v in c.to_tuple()],'forward':[round(v,2) for v in f.to_tuple()],'right':[round(v,2) for v in r.to_tuple()]}
 for name,d in (('fwd',f),('back',f*-1),('right',r),('left',r*-1)):
  p=c+d*150;fl=t(unreal.SystemLibrary.line_trace_single(world,p+V(0,0,50),p-V(0,0,900),TQ,False,[],N,True))
  h=t(unreal.SystemLibrary.line_trace_single(world,c+d*150,c,TQ,False,[],N,True))
  row[name]={'floor_z':round(fl[5].z) if fl else None,'floor_actor':fl[9].get_actor_label() if fl and fl[9] else None,
   'sight_hit_dist_from_art':round((h[5]-c).length()) if h else None,'sight_hit':h[9].get_actor_label() if h and h[9] else None}
 out.append(row)
Path(r'F:\Carnival\Saved\CampaignAcceptance\PrisonTowerArt_20260930.json').write_text(json.dumps(out,indent=1))
