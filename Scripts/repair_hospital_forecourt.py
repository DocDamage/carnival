"""Add a collision-backed paved forecourt to connect road and hospital floor."""
import datetime
import json
import shutil
import sys
from pathlib import Path
import unreal

sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import ROOT, OUT, ROUTE_LEVEL

source = ROOT / "Content/Carnival/World/Levels/L_IndustrialHospitalRoute.umap"
backup = OUT / "Backups" / ("L_IndustrialHospitalRoute_before_forecourt_" +
    datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".umap")
shutil.copy2(source, backup)
world = unreal.EditorLoadingAndSavingUtils.load_map(ROUTE_LEVEL)
if not world:
    raise RuntimeError("Route level failed to load")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
existing = list(actors.get_all_level_actors())
road = next(a for a in existing if a.get_actor_label() == "SM_IndustrialHospital_Road_07")
material = road.static_mesh_component.get_material(0)
if not material:
    raise RuntimeError("Road paving material missing")
label = "Hospital Forecourt Paved Connection"
matches = [a for a in existing if a.get_actor_label() == label]
if len(matches) > 1:
    raise RuntimeError("Duplicate forecourt actors")
actor = matches[0] if matches else actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector())
actor.set_actor_label(label)
component = actor.static_mesh_component
component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
component.set_material(0, material)
component.set_collision_profile_name("BlockAll")
# 22 x 30 metres. Top z=600 meets the hospital floor; the road crown is 14 cm higher.
actor.set_actor_location(unreal.Vector(149900, 0, 580), False, True)
actor.set_actor_scale3d(unreal.Vector(22, 30, .4))
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Forecourt save failed")
(OUT / "Forecourt_Repair.json").write_text(json.dumps({"success": True,
    "backup": str(backup), "actor": actor.get_path_name(), "top_z": 600,
    "route_bounds": [148800,151000,-1500,1500], "material": material.get_path_name()}, indent=2))
