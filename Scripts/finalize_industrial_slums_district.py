"""Replace the demo's world-scale landscape with a district-sized terrain mesh."""
import json
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Slums_District_Finalize.json"
MAP = "/Game/Carnival/World/Levels/L_IndustrialSlums_DistrictFinal"
LAND = "/Game/Carnival/World/Meshes/IndustrialHospital/SM_IndustrialSlums_TerrainPatch"
GROUND = "/Game/IndustrialSlums/Materials/Material_Instances/MI_GroundDisplaced"
report = {"map": MAP}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    landscape_actors = [a for a in eas.get_all_level_actors() if a.get_class().get_name() == "Landscape"]
    report["landscapes_removed"] = len(landscape_actors)
    for actor in landscape_actors:
        if not eas.destroy_actor(actor):
            raise RuntimeError("Could not remove source world-scale landscape")

    mesh = unreal.load_asset(LAND)
    material = unreal.load_asset(GROUND)
    if not mesh or not material:
        raise RuntimeError(f"Terrain assets missing: mesh={bool(mesh)} material={bool(material)}")
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup:
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    terrain = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0))
    if not terrain:
        raise RuntimeError("Could not place local slum terrain")
    terrain.set_actor_label("Industrial Slums Terrain Patch")
    terrain.tags = [unreal.Name("IndustrialHospitalGenerated")]
    component = terrain.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    component.set_material(0, material)
    component.set_collision_profile_name("BlockAll")

    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Saving finalized slum district failed")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    actors = eas.get_all_level_actors()
    report.update({
        "world_after_reopen": world.get_path_name() if world else None,
        "actor_count_after_reopen": len(actors),
        "landscape_count_after_reopen": sum(a.get_class().get_name() == "Landscape" for a in actors),
        "terrain_actor_count": sum(a.get_actor_label() == "Industrial Slums Terrain Patch" for a in actors),
        "phase": "complete",
    })
    if report["landscape_count_after_reopen"] or report["terrain_actor_count"] != 1:
        raise RuntimeError("Finalized district did not reopen with the local terrain patch")
except Exception as exc:
    report["phase"] = "failed"
    report["error"] = repr(exc)
    report["traceback"] = traceback.format_exc()
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_SLUMS_DISTRICT_FINALIZE_" + report["phase"].upper())
unreal.SystemLibrary.quit_editor()
