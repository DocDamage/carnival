"""Read nearby hospital furnishings and candidate sight lines without saving."""
import hashlib,json,math,traceback,sys
from pathlib import Path
import unreal
sys.path.insert(0,str(Path(unreal.Paths.project_dir()).resolve()/'Scripts'))
from industrial_hospital_route_config import MAIN_MAP,HOSPITAL_YAW,hospital_level_transform
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CampaignAcceptance/HospitalRoomSites_20260930'
OUT.mkdir(parents=True,exist_ok=False)
REPORT={'success':False,'errors':[],'assets_saved':False,'furnishings':[],
 'limits':'Editor furnishing locations only; room selection, presentation and runtime approach still require review.'}
try:
 rootfile=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
 before=hashlib.sha256(rootfile.read_bytes()).hexdigest()
 world=unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP);assert world
 origin=hospital_level_transform();a=math.radians(-HOSPITAL_YAW)
 for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  level=actor.get_level().get_path_name()
  if not any(n in level for n in ('Hospital','hospital')):continue
  components=actor.get_components_by_class(unreal.StaticMeshComponent)
  meshes=[c.get_editor_property('static_mesh').get_path_name() for c in components if c.get_editor_property('static_mesh')]
  text=actor.get_actor_label()+' '+' '.join(meshes)
  if not any(n in text.lower() for n in ('bed','desk','cabinet','document','stend','reception','shelf','shelves','computer')):continue
  p=actor.get_actor_location();dx,dy=p.x-origin[0],p.y-origin[1]
  center,extent=actor.get_actor_bounds(False)
  REPORT['furnishings'].append({'label':actor.get_actor_label(),'path':actor.get_path_name(),'meshes':meshes,
   'location_cm':list(p.to_tuple()),'rotation_degrees':list(actor.get_actor_rotation().to_tuple()),
   'hospital_local_cm':[dx*math.cos(a)-dy*math.sin(a),dx*math.sin(a)+dy*math.cos(a),p.z-origin[2]],
   'bounds_origin_cm':list(center.to_tuple()),'bounds_extent_cm':list(extent.to_tuple())})
 REPORT['map_sha256_before']=before;REPORT['map_sha256_after']=hashlib.sha256(rootfile.read_bytes()).hexdigest()
 assert REPORT['map_sha256_after']==before
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
