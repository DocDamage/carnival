"""Bridge the measured floor gap around R11's west-facing tunnel mouth."""
import datetime,json,math,shutil
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion'
REPORT={'success':False,'pieces':[],'limits':'Saved floor connection only; must pass fresh collision graph, continuous production-pawn return and camera/render review.'}
evidence=json.loads((OUT/'Sewer_Handoff_Fine_Candidate.json').read_text())
assert evidence['success'] and not evidence['route_found']
assert evidence['partial_remaining_handoff_gap_cm']==425
assert abs(evidence['partial_floor_points_cm'][-1][1]+10075)<.1
package='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout'
file=ROOT/'Content'/(package.removeprefix('/Game/')+'.umap')
backup=OUT/'Backups'/('SewerR11Floor_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))/file.name
backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,backup)
world=unreal.EditorLoadingAndSavingUtils.load_map(package);assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);rows=list(actors.get_all_level_actors())
owned=unreal.Name('CarnivalInteriorHandoffRepair')
reference=next(a for a in rows if a.get_actor_label()=='SewerStair_PublicFloorHandoff')
material=reference.get_component_by_class(unreal.StaticMeshComponent).get_material(0)
# Source sewer floor ends near y=-10075. The tunnel mouth faces west along
# its -9.43 degree heading. Approach from x=-27300 to avoid its south side
# wall, preserving both existing tunnel walls and the verified R11 interior.
points=[unreal.Vector(-27300,-10100,-1850),unreal.Vector(-27300,-9621,-1782.5),unreal.Vector(-27100,-9654,-1782.5)]
for i,(start,finish) in enumerate(zip(points,points[1:])):
 label='SewerR11_PublicFloorApproach' if i==0 else 'SewerR11_PublicFloorMouth'
 actor=next((a for a in rows if a.get_actor_label()==label),None);assert not actor or owned in actor.tags
 if not actor:actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector())
 actor.modify();actor.set_actor_label(label);actor.set_editor_property('tags',[owned])
 comp=actor.get_component_by_class(unreal.StaticMeshComponent);comp.modify()
 comp.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));comp.set_mobility(unreal.ComponentMobility.STATIC)
 comp.set_collision_profile_name('BlockAll')
 if material:comp.set_material(0,material)
 delta=finish-start;pitch=math.degrees(math.atan2(delta.z,math.hypot(delta.x,delta.y)));yaw=math.degrees(math.atan2(delta.y,delta.x))
 assert abs(pitch)<15
 thickness=25;center=(start+finish)*.5-unreal.Vector(0,0,thickness*.5*math.cos(math.radians(pitch)))
 actor.set_actor_location(center,False,True);actor.set_actor_rotation(unreal.Rotator(pitch=pitch,yaw=yaw,roll=0),True)
 actor.set_actor_scale3d(unreal.Vector((delta.length()+40)/100,2,thickness/100))
 REPORT['pieces'].append({'actor':actor.get_path_name(),'floor_start_cm':start.to_tuple(),'floor_finish_cm':finish.to_tuple(),'pitch_degrees':pitch})
assert unreal.EditorLoadingAndSavingUtils.save_map(world,package)
REPORT.update(success=True,backup=str(backup))
(OUT/'Sewer_R11_Floor_Handoff.json').write_text(json.dumps(REPORT,indent=2))
