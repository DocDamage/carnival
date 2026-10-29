"""Locate foliage roots near the two sign approaches obscured in saved-level views."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion/WayfindingFoliage_20261029_v2.json'
R={'success':False,'errors':[],'regions':{}}
sites={s['id']:s for s in json.loads((ROOT/'Saved/WorldExpansion/Wayfinding_20261029_v5/index.json').read_text())['signs']}
views=json.loads((ROOT/'Saved/WorldExpansion/WayfindingViews_20261029_v5_controlled/index.json').read_text())
REGIONS={s['id']+'_'+s['face']:(sites[s['id']]['base'][:2],s['camera'][:2]) for s in views['shots'] if s['id'] in ('PrisonApproach','EastBoatyard')}
def distance(p,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((p.x-a[0])*dx+(p.y-a[1])*dy)/max(1,dx*dx+dy*dy)))
 return math.hypot(p.x-a[0]-t*dx,p.y-a[1]-t*dy)
try:
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 ea=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for key,(base,eye) in REGIONS.items():
  lo=unreal.Vector(min(base[0],eye[0])-700,min(base[1],eye[1])-700,-2500)
  hi=unreal.Vector(max(base[0],eye[0])+700,max(base[1],eye[1])+700,1800)
  rows=[]
  for actor in ea.get_all_level_actors():
   for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
    mesh=comp.static_mesh
    if not mesh or not any(w in mesh.get_name().lower() for w in ('spruce','tree','pine')):continue
    indices=comp.get_instances_overlapping_box(unreal.Box(min=lo,max=hi),True)
    for i in indices:
     tf=comp.get_instance_transform(i,True);p=tf.translation
     if distance(p,base,eye)>550 or not -2500<=p.z<=1800:continue
     rows.append({'actor':actor.get_path_name(),'component':comp.get_name(),'mesh':mesh.get_path_name(),
       'index':i,'root':p.to_tuple(),'scale':tf.scale3d.to_tuple(),'distance_to_view_line_cm':distance(p,base,eye)})
  R['regions'][key]=rows
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:OUT.write_text(json.dumps(R,indent=2))
