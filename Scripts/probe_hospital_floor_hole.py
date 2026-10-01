"""Read-only: floor along the line the player walked out of BP_Door_01a24 (where PIE fell out of the world)."""
import json,unreal
V=unreal.Vector
w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
a=V(96518,130603,0);b=V(97421,131846,0);R=[]
for i in range(0,41):
 t=i/40;p=a+(b-a)*t;p=p+(b-a).normal()*0
 h=unreal.SystemLibrary.line_trace_single(w,V(p.x,p.y,1000),V(p.x,p.y,-3000),unreal.TraceTypeQuery.ECC_VISIBILITY,True,[],unreal.DrawDebugTrace.NONE,True)
 x=h.to_tuple() if h else None
 R.append([round(p.x),round(p.y),(round(x[5].z),x[9].get_actor_label() if x[9] else None,x[9].get_level().get_outermost().get_name().split('/')[-1] if x[9] else None) if x and x[0] else None])
# Extend beyond the end too
for i in range(1,11):
 p=b+(b-a).normal()*(i*150)
 h=unreal.SystemLibrary.line_trace_single(w,V(p.x,p.y,1000),V(p.x,p.y,-3000),unreal.TraceTypeQuery.ECC_VISIBILITY,True,[],unreal.DrawDebugTrace.NONE,True)
 x=h.to_tuple() if h else None
 R.append([round(p.x),round(p.y),(round(x[5].z),x[9].get_actor_label() if x[9] else None) if x and x[0] else None])
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\HospitalFloorHole_20261001.json','w').write(json.dumps(R,indent=0))
