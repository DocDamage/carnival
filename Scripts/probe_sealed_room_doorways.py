"""Read-only: for the three ground-floor hospital rooms that can be entered only by falling, sweep a standing
capsule through every nearby BP_Door doorway (door actor ignored) along the door's passage axis, and from the
room centre outward in 16 directions, listing what blocks. No saves."""
import json,math,traceback
import unreal
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
ROOMS={'room_A':(95685,130876,643),'room_B':(99379,129948,643),'room_C':(97007,124012,643)}
R={'errors':[]}
def hits(w,a,b,ign):
 out=[]
 for h in unreal.SystemLibrary.capsule_trace_multi(w,a,b,40,85,TQ,False,ign,N,True) or []:
  t=h.to_tuple();x=t[9]
  out.append({'label':x.get_actor_label() if x else '?','comp':t[10].get_name() if t[10] else '','mesh':(t[10].static_mesh.get_name() if isinstance(t[10],unreal.StaticMeshComponent) and t[10].static_mesh else None),'dist':round(t[3]) if isinstance(t[3],float) else None,'blocking':bool(t[0])})
 return out[:4]
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 doors=[a for a in acts if a.get_class().get_name().startswith('BP_Door')]
 for name,(x,y,z) in ROOMS.items():
  c=V(x,y,z+110);rec={'doors':[],'rays':[]}
  for d in doors:
   o=d.get_actor_location()
   if math.hypot(o.x-x,o.y-y)>900 or abs(o.z-(z+120))>200:continue
   fr=[k for k in d.get_components_by_class(unreal.StaticMeshComponent) if k.static_mesh and 'Frame' in k.static_mesh.get_name()]
   fo=unreal.SystemLibrary.get_component_bounds(fr[0])[0] if fr else o
   f=d.get_actor_forward_vector();f.z=0;f=f.normal()
   a=V(fo.x,fo.y,z+110)-f*200;b=V(fo.x,fo.y,z+110)+f*200
   rec['doors'].append({'door':d.get_actor_label(),'frame_centre':[round(v) for v in fo.to_tuple()],'axis':[round(f.x,2),round(f.y,2)],'through':hits(w,a,b,[d])})
  for k in range(16):
   ang=math.radians(k*22.5);e=c+V(math.cos(ang)*900,math.sin(ang)*900,0)
   h=unreal.SystemLibrary.capsule_trace_single(w,c,e,40,85,TQ,False,[],N,True)
   t=h.to_tuple() if h else None
   rec['rays'].append({'deg':k*22.5,'hit':(t[9].get_actor_label() if t and t[0] and t[9] else None),'dist':round(t[3]) if t and t[0] else None})
  R[name]=rec
except Exception:R['errors'].append(traceback.format_exc())
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\SealedRoomDoorways_20261001.json','w').write(json.dumps(R,indent=1))
