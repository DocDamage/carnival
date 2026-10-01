"""Read-only: what lies beyond the two hospital BP_Door_02a doorways (chest-height traces through the doorway, door leaves ignored)."""
import json,unreal
V=unreal.Vector
w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
R={}
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if a.get_actor_label() not in ('BP_Door_02a2','BP_Door_02a7'):continue
 o,e=a.get_actor_bounds(False);rec={'origin':list(o.to_tuple()),'extent':list(e.to_tuple()),'yaw':a.get_actor_rotation().yaw,'comps':{}}
 for c in a.get_components_by_class(unreal.StaticMeshComponent):
  co,ce,_=unreal.SystemLibrary.get_component_bounds(c);rec['comps'][c.get_name()]=[list(co.to_tuple()),list(ce.to_tuple())]
 ax=V(1,0,0) if e.x<e.y else V(0,1,0)
 hits=[]
 for sg in (1,-1):
  for off in (-60,0,60):
   side=V(ax.y,ax.x,0)*off
   for zz in (40,100,160):
    st=o+side-ax*300*sg;st.z=o.z-e.z+zz;en=o+side+ax*300*sg;en.z=st.z
    h=unreal.SystemLibrary.line_trace_multi(w,st,en,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[a],unreal.DrawDebugTrace.NONE,True) or []
    hits.append({'dir':sg,'off':off,'z':zz,'hits':[(x.to_tuple()[9].get_actor_label() if x.to_tuple()[9] else '?',x.to_tuple()[10].get_name() if x.to_tuple()[10] else '',round(((x.to_tuple()[4]-o).dot(ax)))) for x in h]})
 rec['traces']=hits;R[a.get_actor_label()]=rec
open(r'F:\Carnival\Saved\WorldExpansion\DoubleDoorClearance_20261001.json','w').write(json.dumps(R,indent=1))
