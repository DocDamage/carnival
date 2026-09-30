"""Cut one bounded public doorway in the measured copied sewer cross-wall.

Keep wall material, thickness, lower sill and all wall outside the 220x320 cm
opening. Source/vendor map is untouched. Require fresh collision and pawn proof.
"""
import datetime,json,shutil
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion'
REPORT={'success':False,'pieces':[],'limits':'Saved doorway geometry only. Full R11 floor/door/camera/render acceptance remains separate.'}
evidence=json.loads((OUT/'Sewer_Handoff_Fine_Candidate.json').read_text())
assert evidence['success'] and not evidence['route_found']
item=next(x for x in evidence['landing_obstruction_inventory'] if x['actor'].endswith('.StaticMeshActor_369'))
assert item['mesh']=='/Engine/BasicShapes/Cube.Cube'
package='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers'
file=ROOT/'Content'/(package.removeprefix('/Game/')+'.umap')
backup=OUT/'Backups'/('SewerNorthOpening_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))/file.name
backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,backup)
world=unreal.EditorLoadingAndSavingUtils.load_map(package);assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows=list(actors.get_all_level_actors());original=next(a for a in rows if a.get_name()=='StaticMeshActor_369')
component=original.get_component_by_class(unreal.StaticMeshComponent)
assert component.get_editor_property('static_mesh').get_path_name()==item['mesh']
tag=unreal.Name('CarnivalSewerNorthHandoffOpening');offset=unreal.Vector(-27100,-12290,-1800)
if tag not in original.tags:
 center,extent=original.get_actor_bounds(False,True)
 assert unreal.Vector.distance(center+offset,unreal.Vector(*item['bounds_center_cm']))<.1
 assert unreal.Vector.distance(extent,unreal.Vector(*item['bounds_extent_cm']))<.1
 rotation=original.get_actor_rotation()
 assert abs(rotation.pitch)+abs(rotation.roll)+abs(rotation.yaw-90)<.01
 geometry={'center':center.to_tuple(),'extent':extent.to_tuple()}
 unreal.EditorAssetLibrary.set_metadata_tag(original,'CarnivalOriginalWallBounds',json.dumps(geometry))
else:
 geometry=json.loads(unreal.EditorAssetLibrary.get_metadata_tag(original,'CarnivalOriginalWallBounds'))
 center=unreal.Vector(*geometry['center']);extent=unreal.Vector(*geometry['extent'])
material=component.get_material(0);mesh=component.get_editor_property('static_mesh')
left=center.x-extent.x;right=center.x+extent.x;bottom=center.z-extent.z;top=center.z+extent.z
# Level is translated without yaw in the main world. Opening stays on the
# measured R10->R11 route; the floor at this wall is -1850 cm in main space.
door_left=-110;door_right=110;door_bottom=-50;door_top=270
assert left<door_left<door_right<right and bottom<door_bottom<door_top<top
pieces=[('West',(left+door_left)*.5,center.z,door_left-left,top-bottom),
        ('East',(door_right+right)*.5,center.z,right-door_right,top-bottom),
        ('Lintel',0,(door_top+top)*.5,door_right-door_left,top-door_top),
        ('Sill',0,(bottom+door_bottom)*.5,door_right-door_left,door_bottom-bottom)]
for i,(name,x,z,width,height) in enumerate(pieces):
 label='SewerNorthHandoff_Wall_'+name
 actor=original if i==0 else next((a for a in rows if a.get_actor_label()==label),None)
 assert not actor or actor==original or tag in actor.tags,'Reserved label belongs to unrelated actor'
 if not actor:actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector())
 actor.modify();actor.set_actor_label(label);actor.set_editor_property('tags',list(actor.tags)+([tag] if tag not in actor.tags else []))
 comp=actor.get_component_by_class(unreal.StaticMeshComponent);comp.modify();comp.set_static_mesh(mesh)
 comp.set_mobility(unreal.ComponentMobility.STATIC);comp.set_collision_profile_name('BlockAll')
 if material:comp.set_material(0,material)
 actor.set_actor_location(unreal.Vector(x,center.y,z),False,True);actor.set_actor_rotation(unreal.Rotator(yaw=90),True)
 actor.set_actor_scale3d(unreal.Vector(extent.y*2/100,width/100,height/100))
 REPORT['pieces'].append({'actor':actor.get_path_name(),'center_local_cm':[x,center.y,z],'dimensions_cm':[width,extent.y*2,height]})
assert unreal.EditorLoadingAndSavingUtils.save_map(world,package)
REPORT.update(success=True,backup=str(backup),opening_world_cm={'x_min':-27210,'x_max':-26990,'z_min':-1850,'z_max':-1530},original_wall_bounds=geometry)
(OUT/'Sewer_North_Handoff_Opening.json').write_text(json.dumps(REPORT,indent=2))
