"""Open the measured lower-stair handoff in the project-owned sewer copy.

Exact copied props block the measured passenger route. Preserve them in
adjacent open/display positions and add one gentle floor transition. Back up both
maps. Fresh collision survey and actual pawn traversal are separate requirements.
"""
import datetime,json,math,shutil
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion'
REPORT={'success':False,'changes':[],'backups':[],
    'limits':'Saved bounded geometry changes only; requires fresh pawn round trip, camera and rendered review. Does not add interactive door behavior.'}
SEWER='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers'
CONNECTOR='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout'
evidence=json.loads((OUT/'Sewer_Handoff_Fine_Candidate.json').read_text())
assert evidence['success'] and not evidence['route_found']
inventory={a['actor'].split('.')[-1]:a for a in evidence['landing_obstruction_inventory']}
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
backup=OUT/'Backups'/('Sewer_Handoff_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
for package in (SEWER,CONNECTOR):
    file=ROOT/'Content'/(package.removeprefix('/Game/')+'.umap')
    destination=backup/file.name;destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(file,destination);REPORT['backups'].append(str(destination))
world=unreal.EditorLoadingAndSavingUtils.load_map(SEWER);assert world
rows={a.get_name():a for a in actors.get_all_level_actors()}
offset=unreal.Vector(-27100,-12290,-1800)
tag=unreal.Name('CarnivalSewerHandoffClearance')
for name,mesh_name,delta in (
        ('StaticMeshActor_7','SM_Sewer_Tube_Gate_01a',unreal.Vector(-300,0,0)),
        ('StaticMeshActor_373','SM_Sewer_Wall_Beam_01c',unreal.Vector(-150,0,0)),
        ('StaticMeshActor_320','SM_Sewer_Wall_Brick_01a',unreal.Vector(250,0,0)),
        ('StaticMeshActor_328','SM_Sewer_Wall_Brick_01a',unreal.Vector(250,0,0))):
    actor=rows[name];component=actor.get_component_by_class(unreal.StaticMeshComponent)
    assert component.get_editor_property('static_mesh').get_name()==mesh_name
    before=actor.get_actor_location()
    if tag not in actor.tags:
        assert unreal.Vector.distance(before+offset,unreal.Vector(*inventory[name]['location_cm']))<.1,(name,before)
        actor.modify();actor.set_actor_location(before+delta,False,True)
        actor.set_editor_property('tags',list(actor.tags)+[tag])
    REPORT['changes'].append({'actor':actor.get_path_name(),'before_local_cm':before.to_tuple(),
        'after_local_cm':actor.get_actor_location().to_tuple(),'delta_world_cm':delta.to_tuple()})
assert unreal.EditorLoadingAndSavingUtils.save_map(world,SEWER)
world=unreal.EditorLoadingAndSavingUtils.load_map(CONNECTOR);assert world
rows=list(actors.get_all_level_actors())
label='SewerStair_PublicFloorHandoff';owned=unreal.Name('CarnivalInteriorHandoffRepair')
actor=next((a for a in rows if a.get_actor_label()==label),None)
assert not actor or owned in actor.tags,'Unrelated actor has reserved handoff label'
reference=next(a for a in rows if a.get_name()=='StaticMeshActor_923')
material=reference.get_component_by_class(unreal.StaticMeshComponent).get_material(0)
if not actor:actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector())
actor.modify();actor.set_actor_label(label);actor.set_editor_property('tags',[owned])
component=actor.get_component_by_class(unreal.StaticMeshComponent);component.modify()
component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
component.set_mobility(unreal.ComponentMobility.STATIC);component.set_collision_profile_name('BlockAll')
if material:component.set_material(0,material)
start=unreal.Vector(-26940,-12585,-1758);finish=unreal.Vector(-26940,-12100,-1850)
delta=finish-start;pitch=math.degrees(math.atan2(delta.z,math.hypot(delta.x,delta.y)))
thickness=25;center=(start+finish)*.5-unreal.Vector(0,0,thickness*.5*math.cos(math.radians(pitch)))
actor.set_actor_location(center,False,True)
actor.set_actor_rotation(unreal.Rotator(pitch=pitch,yaw=90,roll=0),True)
actor.set_actor_scale3d(unreal.Vector((delta.length()+40)/100,1.4,thickness/100))
assert abs(pitch)<15
assert unreal.EditorLoadingAndSavingUtils.save_map(world,CONNECTOR)
REPORT.update(success=True,floor_actor=actor.get_path_name(),floor_start_cm=start.to_tuple(),
    floor_end_cm=finish.to_tuple(),pitch_degrees=pitch)
(OUT/'Sewer_Handoff_Clearance_Repair.json').write_text(json.dumps(REPORT,indent=2))
