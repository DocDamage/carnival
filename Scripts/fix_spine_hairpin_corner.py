"""Replace the outer spine's Catmull overshoot lobe (controls 4-6) with a flat corner slab.

Slabs 473/474 form a ~15 m south-east lobe between slab 472 (eastbound, end top ~1423) and slab
475 (northbound, start top ~1423); vehicles cannot turn its 141-degree hairpin and catch on its
seams. The lobe is removed and one flat slab (top 1423, 760 cm wide) spans from 472's end across
475's start plus a half-width turning pad. Only the connectors level is saved (backed up).
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_CarnivalWorldExpansion_Connections_Layout'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/SpineHairpinFix_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;HALF_T=22.5;TOP=1423.0
R={'success':False,'errors':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 R.update(level_sha256_before=sha(LEVEL_FILE),map_sha256_before=sha(MAPFILE));shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_hairpin_fix.umap'))
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 by={a.get_name():a for a in EA.get_all_level_actors() if a.get_actor_label()=='OuterRoute_Segment' and '/'+LEVEL+'.' in a.get_path_name()}
 s472,s475=by['StaticMeshActor_472'],by['StaticMeshActor_475']
 def end_xy(a,sign):
  c=a.get_actor_location();f=a.get_actor_forward_vector();L=a.get_actor_scale3d().x*50
  return (c.x+f.x*L*sign,c.y+f.y*L*sign)
 e472=end_xy(s472,1)   # 472 points east (yaw ~0): +forward is its east end
 st475=end_xy(s475,-1) # 475 points north (yaw ~91): -forward is its south start
 x0=e472[0];x1=st475[0]+380.0;y=(e472[1]+st475[1])/2
 R['lobe_removed']=[]
 for n in ('StaticMeshActor_473','StaticMeshActor_474'):
  a=by[n];o,e=a.get_actor_bounds(False);R['lobe_removed'].append({'name':n,'origin':list(o.to_tuple()),'extent':list(e.to_tuple()),'yaw':a.get_actor_rotation().yaw});EA.destroy_actor(a)
 assert LE.set_current_level_by_name(LEVEL)
 corner=EA.spawn_actor_from_class(unreal.StaticMeshActor,V((x0+x1)/2,y,TOP-HALF_T),unreal.Rotator(roll=0.0,pitch=0.0,yaw=0.0))
 src=s472.static_mesh_component
 corner.static_mesh_component.set_static_mesh(src.static_mesh)
 for i,m in enumerate(src.get_materials()):corner.static_mesh_component.set_material(i,m)
 corner.static_mesh_component.set_collision_profile_name(src.get_collision_profile_name())
 corner.set_actor_scale3d(V((x1-x0)/100.0,7.6,0.45))
 corner.set_actor_label('OuterRoute_Segment');corner.set_folder_path(s472.get_folder_path())
 assert '/'+LEVEL+'.' in corner.get_path_name()
 R['corner']={'name':corner.get_name(),'from_x':x0,'to_x':x1,'y':y,'top':TOP,'e472':e472,'st475':st475}
 assert unreal.EditorLoadingAndSavingUtils.save_packages([s472.get_outermost()],False)
 R.update(level_sha256_after=sha(LEVEL_FILE),map_sha256_after=sha(MAPFILE));assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
