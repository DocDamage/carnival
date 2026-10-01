"""Read-only: on each hospital stairwell's flights and landings (50 cm grid), which actors block a standing player."""
import collections,json,unreal
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
vols=[a for a in acts if isinstance(a,unreal.BlockingVolume) and 'Hospital' in a.get_level().get_outermost().get_name()]
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
WELLS={'well_1':(94877,124757,95778,125603),'well_2':(100155,126384,101001,127285)}
out={}
for k,(x0,y0,x1,y1) in WELLS.items():
 blockers=collections.Counter();cells=0;clear=0
 for x in range(x0,x1+1,50):
  for y in range(y0,y1+1,50):
   top=1600
   for _ in range(8):
    h=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,top),V(x,y,550),TQ,False,vols,N,True))
    if not h:break
    lab=h[9].get_actor_label() if h[9] else ''
    if h[7].z>=.7 and lab.startswith(('SM_Ladder_0','SM_Ladder_Floor')):
     cells+=1;c=V(x,y,h[5].z+112)
     b=t(unreal.SystemLibrary.capsule_trace_single(world,c,c+V(0,0,.1),42,80,TQ,False,vols,N,True))
     if b:blockers[b[9].get_actor_label() if b[9] else '?']+=1
     else:clear+=1
    top=h[5].z-40
 out[k]={'stair_cells':cells,'clear':clear,'blockers':blockers.most_common()}
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\StairwellObstructions.json','w').write(json.dumps(out,indent=1))
