"""Relocate the copied upper sewer wall intersecting the measured stair exit."""
import datetime, json, shutil
from pathlib import Path
import unreal

root=Path(r'F:\Carnival'); out=root/'Saved/WorldExpansion'
package='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers'
world=unreal.EditorLoadingAndSavingUtils.load_map(package)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
wall=next(a for a in actors.get_all_level_actors() if a.get_name()=='StaticMeshActor_323')
component=wall.get_component_by_class(unreal.StaticMeshComponent)
assert component.get_editor_property('static_mesh').get_name()=='SM_Sewer_Wall_Brick_01b'
tag=unreal.Name('StairLandingClearanceMoved')
backup=out/'Backups'/('Sewers_before_landing_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.umap')
shutil.copy2(root/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers.umap',backup)
before=wall.get_actor_location()
if tag not in wall.get_editor_property('tags'):
    wall.set_actor_location(before+unreal.Vector(350,0,0),False,True)
    wall.set_editor_property('tags',list(wall.get_editor_property('tags'))+[tag])
assert unreal.EditorLoadingAndSavingUtils.save_map(world,package)
beam_changes=[]
for name, offset in [('StaticMeshActor_339',350),('StaticMeshActor_340',-350),('StaticMeshActor_66',350),('StaticMeshActor_245',350)]:
    beam=next(a for a in actors.get_all_level_actors() if a.get_name()==name)
    comp=beam.get_component_by_class(unreal.StaticMeshComponent)
    expected='SM_Sewer_Wall_Arch_01a' if name in ('StaticMeshActor_66','StaticMeshActor_245') else 'SM_Sewer_Wall_Beam_01b'
    assert comp.get_editor_property('static_mesh').get_name()==expected
    old=beam.get_actor_location()
    if tag not in beam.get_editor_property('tags'):
        beam.set_actor_location(old+unreal.Vector(offset,0,0),False,True)
        beam.set_editor_property('tags',list(beam.get_editor_property('tags'))+[tag])
    beam_changes.append({'actor':beam.get_path_name(),'before':old.to_tuple(),'after':beam.get_actor_location().to_tuple()})
assert unreal.EditorLoadingAndSavingUtils.save_map(world,package)
(out/'Sewer_Stair_Landing_Repair.json').write_text(json.dumps({'saved':True,'backup':str(backup),
    'actor':wall.get_path_name(),'before':before.to_tuple(),'after':wall.get_actor_location().to_tuple(),'beams':beam_changes,
    'acceptance':'Requires both-direction player traversal'},indent=2))
unreal.SystemLibrary.quit_editor()
