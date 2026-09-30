"""Raise one measured overhead vent in the owned sewer copy; preserve collision."""
import datetime,json,shutil
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion'
REPORT={'success':False,'limits':'One saved overhead prop correction; actual pawn round trip and full R11 route remain separate.'}
evidence=json.loads((OUT/'Sewer_Handoff_Fine_Candidate.json').read_text())
assert evidence['success'] and not evidence['route_found']
item=next(x for x in evidence['landing_obstruction_inventory'] if x['actor'].endswith('.StaticMeshActor_114'))
package='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers'
file=ROOT/'Content'/(package.removeprefix('/Game/')+'.umap')
backup=OUT/'Backups'/('SewerVent_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))/file.name
backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,backup)
world=unreal.EditorLoadingAndSavingUtils.load_map(package);assert world
actor=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_name()=='StaticMeshActor_114')
component=actor.get_component_by_class(unreal.StaticMeshComponent)
assert component.get_editor_property('static_mesh').get_path_name()==item['mesh']
before=actor.get_actor_location();tag=unreal.Name('CarnivalSewerVentClearance')
if tag not in actor.tags:
    assert unreal.Vector.distance(before+unreal.Vector(-27100,-12290,-1800),unreal.Vector(*item['location_cm']))<.1
    actor.modify();actor.set_actor_location(before+unreal.Vector(0,0,100),False,True)
    actor.set_editor_property('tags',list(actor.tags)+[tag])
assert component.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION
assert unreal.EditorLoadingAndSavingUtils.save_map(world,package)
REPORT.update(success=True,actor=actor.get_path_name(),backup=str(backup),before_local_cm=before.to_tuple(),
              after_local_cm=actor.get_actor_location().to_tuple(),collision_preserved=True)
(OUT/'Sewer_Landing_Vent_Repair.json').write_text(json.dumps(REPORT,indent=2))
