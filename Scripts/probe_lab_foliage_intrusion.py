"""Read-only: find foliage/tree instances whose location lies inside the Lab A/B footprints."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
A=(-42097.962876199206,-7043.716818882417,600.0);YAW=-57.0
def local(v):
 x,y=v.x-A[0],v.y-A[1];c,s=math.cos(math.radians(-YAW)),math.sin(math.radians(-YAW));return (c*x-s*y,s*x+c*y)
def inside(v):
 lx,ly=local(v);return -4350<=lx<=1500 and -750<=ly<=1550
R={'success':False,'errors':[],'components':[]}
try:
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  for comp in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
   n=comp.get_instance_count()
   hits=[]
   for i in range(n):
    tr=comp.get_instance_transform(i,True);p=tr.translation
    if inside(p) and -1500<p.z<1400:hits.append([i,[round(v) for v in p.to_tuple()]])
   if hits:R['components'].append({'actor':a.get_actor_label(),'actor_class':a.get_class().get_name(),'level':a.get_level().get_outermost().get_name(),
    'component':comp.get_name(),'component_class':comp.get_class().get_name(),'mesh':comp.static_mesh.get_path_name() if comp.static_mesh else None,'instances':hits})
  if isinstance(a,unreal.StaticMeshActor) and inside(a.get_actor_location()) and 'Lab' not in a.get_level().get_outermost().get_name():
   m=a.static_mesh_component.static_mesh
   R['components'].append({'actor':a.get_actor_label(),'actor_class':'StaticMeshActor','level':a.get_level().get_outermost().get_name(),'mesh':m.get_path_name() if m else None,'location':[round(v) for v in a.get_actor_location().to_tuple()]})
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(ROOT/'Saved/CampaignAcceptance/LabFoliageIntrusionAnyHeight_20260930.json').write_text(json.dumps(R,indent=1))
