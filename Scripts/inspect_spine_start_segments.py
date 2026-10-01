import json,math,unreal
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
out=[]
segs={a.get_name():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='OuterRoute_Segment'}
for i in range(9):
 a=segs['StaticMeshActor_%d'%i];r=a.get_actor_rotation();f=a.get_actor_forward_vector();s=a.get_actor_scale3d()
 out.append({'name':a.get_name(),'loc':list(a.get_actor_location().to_tuple()),'roll':r.roll,'pitch':r.pitch,'yaw':r.yaw,'scale':list(s.to_tuple()),'forward':list(f.to_tuple()),
  'mesh_extent':list(a.static_mesh_component.static_mesh.get_bounds().box_extent.to_tuple())})
open(r'F:\Carnival\Saved\WorldExpansion\SpineStartSegments_20261001.json','w').write(json.dumps(out,indent=1))
