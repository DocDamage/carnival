"""Give the stationary sail assembly a valid kinematic mast attachment body."""
import datetime,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion'
package='/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=OUT/'Backups'/('L_CarnivalWorldExpansion_Shipwreck_before_sail_root_'+stamp+'.umap')
shutil.copy2(ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck.umap',backup)
report={'success':False,'backup':str(backup)}
try:
    world=unreal.EditorLoadingAndSavingUtils.load_map(package)
    actor=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='SM_Sails_Torn')
    comp=actor.get_component_by_class(unreal.SkeletalMeshComponent); mesh=comp.get_skinned_asset()
    if comp.is_simulating_physics(): raise RuntimeError('Expected stationary sail assembly; refusing to alter simulation')
    # Existing attachment is 23 m above the passage; do not fill the whole sail
    # bounding box, which would block empty space between several cloth pieces.
    anchor=comp.get_socket_location('Sails_Torn')
    integrated_anchor=anchor+unreal.Vector(-6033.089,-10010,-2108.649)
    if integrated_anchor.z < -1000: raise RuntimeError('Root attachment is unexpectedly near underground player routes')
    report.update(mesh=mesh.get_path_name(),root_bone='Sails_Torn',root_world_cm=integrated_anchor.to_tuple(),collision_before=str(comp.get_collision_enabled()),simulation_before=False,anchor_radius_cm=10,body_type='Kinematic',scope='Rigid mast attachment initialization; cloth appearance and animation unchanged; no full-sail bounds collider')
    asset=unreal.CarnivalRouteEditorLibrary.create_sail_anchor_collision(mesh,'/Game/Carnival/World/Physics/PA_ShipwreckSailAnchor')
    if not asset: raise RuntimeError('Could not author valid sail root body')
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset): raise RuntimeError('Could not save project physics asset')
    comp.set_physics_asset(asset,True)
    if comp.is_simulating_physics() or str(comp.get_collision_enabled())!=report['collision_before']: raise RuntimeError('Collision policy unexpectedly changed')
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,package): raise RuntimeError('Cannot save Shipwreck copy')
    report.update(success=True,physics_asset=asset.get_path_name(),collision_after=str(comp.get_collision_enabled()),simulation_after=comp.is_simulating_physics())
except Exception:
    report['error']=traceback.format_exc(); unreal.log_error(report['error'])
finally:
    (OUT/'Shipwreck_Sail_Root_Repair.json').write_text(json.dumps(report,indent=2))
    unreal.SystemLibrary.quit_editor()
