"""Place the supplied factory exit-gate facade outside the hospital."""
import json
import traceback
from pathlib import Path
import unreal
import sys
sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import FACADE_LOCAL

ROOT = Path(r"F:\Carnival")
REPORT_PATH = ROOT / "Saved/IndustrialHospital/Hospital_Facade_Authoring.json"
LEVEL = "/Game/Carnival/World/Levels/L_IndustrialHospitalExterior"
LEVEL_FILE = ROOT / "Content/Carnival/World/Levels/L_IndustrialHospitalExterior.umap"
LOCAL = FACADE_LOCAL
report = {"phase": "starting"}


def add_lamp(eas, name, location):
    actor = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location))
    actor.set_actor_label(name)
    light = actor.get_editor_property("light_component")
    light.set_editor_property("intensity", 2200.0)
    light.set_editor_property("attenuation_radius", 3200.0)
    light.set_editor_property("light_color", unreal.Color(r=255, g=61, b=23, a=255))
    light.set_editor_property("cast_shadows", False)
    return actor


try:
    if LEVEL_FILE.exists():
        world = unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
        if not world:
            raise RuntimeError("Could not open facade level")
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in list(eas.get_all_level_actors()):
            if actor.get_class().get_name() != "WorldSettings":
                eas.destroy_actor(actor)
    else:
        if not unreal.EditorLevelLibrary.new_level(LEVEL):
            raise RuntimeError("Could not create facade level")
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in list(eas.get_all_level_actors()):
            if actor.get_class().get_name() != "WorldSettings":
                eas.destroy_actor(actor)

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mesh_path = "/Game/IndustrialSlums/IndustrialHospital_Facade/SM_IndustrialHospital_FactoryFacade"
    material_path = "/Game/IndustrialSlums/Materials/MI_ConcreteWall"
    mesh, material = unreal.load_asset(mesh_path), unreal.load_asset(material_path)
    if not mesh or not material:
        raise RuntimeError("Facade mesh or concrete material is missing")
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup:
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*LOCAL), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    actor.set_actor_label("Abandoned Hospital Factory-Gate Facade")
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    component.set_collision_profile_name("BlockAll")
    for index in range(len(mesh.get_editor_property("static_materials"))):
        component.set_material(index, material)

    add_lamp(eas, "Gate Sodium Lamp West", (LOCAL[0] - 3500.0, LOCAL[1] + 800.0, LOCAL[2] + 1200.0))
    add_lamp(eas, "Gate Sodium Lamp East", (LOCAL[0] + 3500.0, LOCAL[1] + 800.0, LOCAL[2] + 1200.0))
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Could not save hospital facade level")
    report.update({"phase": "complete", "level": LEVEL, "mesh": mesh_path, "material": material_path, "facade_local": LOCAL, "yaw": 90.0})
except Exception as exc:
    report["phase"] = "failed"
    report["error"] = repr(exc)
    report["traceback"] = traceback.format_exc()
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("HOSPITAL_FACADE_AUTHORING_" + report["phase"].upper())
unreal.SystemLibrary.quit_editor()
