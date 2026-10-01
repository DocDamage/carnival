"""Remove the showcase rock blocking the outer spine and trim the Prison's 5 km ground strip.

After the Prison sublevel was turned upright, SM_Rocks_05 (63 x 29 m) lies across the outer
spine (PIE walk stalled at (-34309,-29485)). Plane2, the Prison's walkable ground, is a 5 km x
200 m collision sheet at z 580 crossing the world diagonally; it is trimmed along its long axis
to the Prison footprint plus 50 m. Only the Prison level is saved (backed up first).
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_CarnivalWorldExpansion_Prison'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison.umap'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/PrisonRouteBlockers_20261001';OUT.mkdir(parents=True,exist_ok=False)
R={'success':False,'errors':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 R.update(level_sha256_before=sha(LEVEL_FILE),map_sha256_before=sha(MAPFILE));shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_route_blockers.umap'))
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 mine=[a for a in EA.get_all_level_actors() if '/'+LEVEL+'.' in a.get_path_name()]
 by={a.get_actor_label():a for a in mine}
 rock=by['SM_Rocks_05'];o,e=rock.get_actor_bounds(False)
 R['removed']={'label':'SM_Rocks_05','mesh':rock.static_mesh_component.static_mesh.get_path_name(),'origin':list(o.to_tuple()),'extent':list(e.to_tuple()),
  'location':list(rock.get_actor_location().to_tuple()),'rotation':list(rock.get_actor_rotation().to_tuple()),'scale':list(rock.get_actor_scale3d().to_tuple())}
 EA.destroy_actor(rock)
 plane=by['Plane2'];p=plane.get_actor_location();yaw=math.radians(plane.get_actor_rotation().yaw)
 ax=(math.cos(yaw),math.sin(yaw))
 # Prison footprint along the plane's long axis (excluding the Plane actors themselves).
 ts=[]
 for a in mine:
  if a.get_actor_label().startswith('Plane') or not a.get_level():continue
  ao,ae=a.get_actor_bounds(False)
  if ae.length()<1 or ae.length()>20000:continue
  for sx in (-1,1):
   for sy in (-1,1):
    ts.append((ao.x+sx*ae.x-p.x)*ax[0]+(ao.y+sy*ae.y-p.y)*ax[1])
 lo,hi=min(ts)-5000,max(ts)+5000
 s=plane.get_actor_scale3d();mesh_half=50.0  # engine Plane is 100 cm square
 R['plane2_before']={'location':list(p.to_tuple()),'scale':list(s.to_tuple()),'length_cm':s.x*2*mesh_half}
 mid=(lo+hi)/2;plane.modify()
 plane.set_actor_location(unreal.Vector(p.x+ax[0]*mid,p.y+ax[1]*mid,p.z),False,True)
 plane.set_actor_scale3d(unreal.Vector((hi-lo)/(2*mesh_half),s.y,s.z))
 R['plane2_after']={'location':list(plane.get_actor_location().to_tuple()),'scale':list(plane.get_actor_scale3d().to_tuple()),'length_cm':hi-lo,'footprint_axis_range_cm':[lo+5000,hi-5000]}
 assert unreal.EditorLoadingAndSavingUtils.save_packages([plane.get_outermost()],False)
 R.update(level_sha256_after=sha(LEVEL_FILE),map_sha256_after=sha(MAPFILE));assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
