"""Read-only: Lab A step piece mesh/transform (in Lab A local frame) and the capsule blocking the west opening."""
import json,math
from pathlib import Path
import unreal
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
A=(-42097.962876199206,-7043.716818882417,600.0);YAW=-57.0
def loc(v):
 x,y=v.x-A[0],v.y-A[1];c,s=math.cos(math.radians(-YAW)),math.sin(math.radians(-YAW));return [round(c*x-s*y,1),round(s*x+c*y,1),round(v.z-A[2],1)]
out=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if 'L_CarnivalWorldExpansion_LabA.' not in a.get_path_name():continue
 l=a.get_actor_label()
 if not (l.startswith('SM_MStair01-Steps') or l.startswith('SM_MFloor02-Steps') or l.startswith('SM_MFloor02-StepsSide') or l.startswith('BP_LabCapsule11')):continue
 r=a.get_actor_rotation();o,e=a.get_actor_bounds(False)
 row={'label':l,'class':a.get_class().get_name(),'local_location':loc(a.get_actor_location()),'local_yaw':round(r.yaw-YAW,1),'pitch':r.pitch,'roll':r.roll,
  'scale':list(a.get_actor_scale3d().to_tuple()),'bounds_origin_local':loc(o),'bounds_extent_world':[round(v) for v in e.to_tuple()]}
 if isinstance(a,unreal.StaticMeshActor):
  m=a.static_mesh_component.static_mesh;b=m.get_bounds();row.update(mesh=m.get_path_name(),mesh_origin=list(b.origin.to_tuple()),mesh_extent=list(b.box_extent.to_tuple()))
 out.append(row)
Path(r'F:\Carnival\Saved\CampaignAcceptance\LabStepAndCapsule_20260930.json').write_text(json.dumps(out,indent=1))
