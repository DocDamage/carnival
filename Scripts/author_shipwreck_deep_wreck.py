"""Sink the Shipwreck 29 m and load the wreck itself.

The wreck (vendor Ship / SetDressing_Interior / SetDressing_Exterior sublevels) was only referenced from inside
L_CarnivalWorldExpansion_Shipwreck, and nested streaming levels are ignored, so it never loaded. At the old depth
the 28 m hull would also have stood up through the Atlantis floor and the ground above.

This script:
1. Copies the three vendor sublevels into /Game/Carnival/World/Levels (vendor pack untouched) and removes the two
   masts from the hull copy (the main mast alone is 46 m tall).
2. Moves the Shipwreck region streaming offset from z -2108.649 to -5008.649 and streams the three copies at the same
   offset, so region dressing (seabed, debris, manifest station, torn sails) keeps its place around the hull.
3. In the Connections level: removes the old 14 m R12 tunnel boxes that sat in the Atlantis floor opening, then
   builds a sealed rock cavern around the wreck whose ceiling keeps one shaft open under that opening, a flooded
   cavern water volume (priority below the Atlantis hall so the hall surface and lid are unchanged) and three
   cavern lights. R12 becomes a swim down the shaft onto the main deck.
Backs up LV_Carnival and the Connections level; the region map and vendor packages must stay byte-identical.
"""
import gc
import hashlib
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/WorldExpansion/ShipwreckDeep_20261001"
OUT.mkdir(parents=True, exist_ok=False)
LEVEL_DIR = "/Game/Carnival/World/Levels"
MAIN_MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
MAIN_FILE = ROOT / "Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap"
REGION = LEVEL_DIR + "/L_CarnivalWorldExpansion_Shipwreck"
CONN = "L_CarnivalWorldExpansion_Connections_Layout"
COPIES = {  # vendor sublevel -> project copy
    "/Game/UnderwaterShip/Levels/Sublevels/Ship": LEVEL_DIR + "/L_CarnivalWorldExpansion_ShipwreckHull",
    "/Game/UnderwaterShip/Levels/Sublevels/SetDressing_Interior": LEVEL_DIR + "/L_CarnivalWorldExpansion_ShipwreckDressingInterior",
    "/Game/UnderwaterShip/Levels/Sublevels/SetDressing_Exterior": LEVEL_DIR + "/L_CarnivalWorldExpansion_ShipwreckDressingExterior",
}
MASTS = ("Ship_MastDeck_BP", "Ship_MastStern_BP")
OLD_OFFSET = (-6033.089, -10010.0, -2108.649)
NEW_OFFSET = (-6033.089, -10010.0, -5008.649)

# Cavern (world cm). Ceiling sits just under the Atlantis floor (exit pad bottom -1950); the forecastle top is -2050.
CAV_X, CAV_Y = (-10400.0, -3000.0), (-12400.0, -5900.0)
FLOOR_TOP, CEIL_BOTTOM, CEIL_TOP = -5200.0, -1990.0, -1870.0
SHAFT_X, SHAFT_Y = (-7100.0, -5650.0), (-11300.0, -9500.0)  # existing Atlantis floor opening, over the main deck
WALL = 100.0
TAG = "ShipwreckDeepCavern"

V = unreal.Vector
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
ROCK = unreal.load_asset("/Game/Docks/VOL2_Powell/Materials/Instances/MI_Rock_29a")
R = {"success": False, "errors": [], "copies": [], "removed_masts": [], "removed_r12": [], "spawned": [], "intruders": []}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pkg_file(package):
    return ROOT / ("Content" + package[len("/Game"):] + ".umap")


def transform(offset):
    t = unreal.Transform()
    t.set_editor_property("translation", V(*offset))
    t.set_editor_property("rotation", unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0).quaternion())
    t.set_editor_property("scale3d", V(1.0, 1.0, 1.0))
    return t


def tag(actor, label):
    actor.set_actor_label(label)
    tags = list(actor.get_editor_property("tags"))
    tags += [unreal.Name("WorldExpansionGenerated"), unreal.Name(TAG)]
    actor.set_editor_property("tags", tags)
    R["spawned"].append(label)
    return actor


def box(lo, hi, label):
    c = V((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, c, unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    assert a and "/" + CONN + "." in a.get_path_name(), "box spawned outside the Connections level"
    comp = a.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_editor_property("static_mesh", CUBE)
    comp.set_material(0, ROCK)
    comp.set_collision_profile_name("BlockAll")
    a.set_actor_scale3d(V((hi[0] - lo[0]) / 100.0, (hi[1] - lo[1]) / 100.0, (hi[2] - lo[2]) / 100.0))
    return tag(a, label)


def light(loc, label):
    a = EAS.spawn_actor_from_class(unreal.PointLight, V(*loc), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    comp = a.get_component_by_class(unreal.PointLightComponent)
    comp.set_editor_property("intensity", 1400.0)
    comp.set_editor_property("attenuation_radius", 2800.0)
    comp.set_editor_property("light_color", unreal.Color(r=92, g=168, b=205, a=255))
    comp.set_editor_property("cast_shadows", False)
    return tag(a, label)


try:
    guarded = [pkg_file(REGION)] + [pkg_file(v) for v in COPIES]
    R["hash_before"] = {str(p): sha(p) for p in guarded}
    for dest in COPIES.values():
        assert not unreal.EditorAssetLibrary.does_asset_exist(dest), "already authored: " + dest
    conn_file = pkg_file(LEVEL_DIR + "/" + CONN)
    for f in (MAIN_FILE, MAIN_FILE.with_name("LV_Carnival_BuiltData.uasset"), conn_file):
        if f.exists():
            shutil.copy2(f, OUT / (f.stem + ".before_shipwreck_deep" + f.suffix))
    R["main_sha256_before"] = sha(MAIN_FILE)

    # 1. Project copies of the vendor wreck sublevels; masts removed from the hull copy.
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    for src, dest in COPIES.items():
        clone = tools.duplicate_asset(dest.rsplit("/", 1)[1], LEVEL_DIR, unreal.load_asset(src))
        assert clone and unreal.EditorAssetLibrary.save_loaded_asset(clone, False), "copy failed: " + dest
        R["copies"].append({"source": src, "copy": dest})
        clone = None
    gc.collect()
    hull = COPIES["/Game/UnderwaterShip/Levels/Sublevels/Ship"]
    world = unreal.EditorLoadingAndSavingUtils.load_map(hull)
    for a in list(EAS.get_all_level_actors()):
        if a.get_actor_label() in MASTS:
            R["removed_masts"].append(a.get_actor_label())
            EAS.destroy_actor(a)
    assert sorted(R["removed_masts"]) == sorted(MASTS), "mast actors not found: " + str(R["removed_masts"])
    assert unreal.EditorLoadingAndSavingUtils.save_map(world, hull), "hull copy save failed"
    world = None
    gc.collect()

    # 2. Stream the copies and sink the region, all at the same offset.
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    assert world
    region = unreal.GameplayStatics.get_streaming_level(world, REGION)
    assert region, "Shipwreck region is not streamed"
    old = tuple(round(v, 3) for v in region.get_editor_property("level_transform").translation.to_tuple())
    assert old == OLD_OFFSET, "unexpected region offset " + str(old)
    region.modify()
    region.set_editor_property("level_transform", transform(NEW_OFFSET))
    for dest in COPIES.values():
        s = unreal.EditorLevelUtils.add_level_to_world_with_transform(world, dest, unreal.LevelStreamingAlwaysLoaded, transform(NEW_OFFSET))
        assert s, "could not stream " + dest
        s.set_editor_property("should_be_loaded", True)
        s.set_editor_property("should_be_visible", True)
    R["region_offset"] = {"old": OLD_OFFSET, "new": NEW_OFFSET}

    # 3. Connections level: drop the old R12 tunnel boxes, build the cavern, water and lights.
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name(CONN)
    for a in list(EAS.get_all_level_actors()):
        label = a.get_actor_label()
        if label.startswith("AtlantisToShipwreckPassage_") and a.get_class().get_name() == "StaticMeshActor":
            R["removed_r12"].append(label)
            EAS.destroy_actor(a)
    assert len(R["removed_r12"]) == 8, "expected 8 R12 tunnel boxes, found " + str(len(R["removed_r12"]))

    x0, x1 = CAV_X
    y0, y1 = CAV_Y
    zb = FLOOR_TOP - 200.0
    box((x0 - WALL, y0 - WALL, zb), (x1 + WALL, y1 + WALL, FLOOR_TOP), "ShipwreckCavern_Floor")
    box((x0 - WALL, y0 - WALL, zb), (x0, y1 + WALL, CEIL_TOP), "ShipwreckCavern_WallWest")
    box((x1, y0 - WALL, zb), (x1 + WALL, y1 + WALL, CEIL_TOP), "ShipwreckCavern_WallEast")
    box((x0, y0 - WALL, zb), (x1, y0, CEIL_TOP), "ShipwreckCavern_WallSouth")
    box((x0, y1, zb), (x1, y1 + WALL, CEIL_TOP), "ShipwreckCavern_WallNorth")
    sx0, sx1 = SHAFT_X
    sy0, sy1 = SHAFT_Y
    box((x0, y0, CEIL_BOTTOM), (sx0, y1, CEIL_TOP), "ShipwreckCavern_CeilingWest")
    box((sx1, y0, CEIL_BOTTOM), (x1, y1, CEIL_TOP), "ShipwreckCavern_CeilingEast")
    box((sx0, y0, CEIL_BOTTOM), (sx1, sy0, CEIL_TOP), "ShipwreckCavern_CeilingSouth")
    box((sx0, sy1, CEIL_BOTTOM), (sx1, y1, CEIL_TOP), "ShipwreckCavern_CeilingNorth")

    w = EAS.spawn_actor_from_class(unreal.CarnivalWaterVolume,
                                   V((x0 + x1) / 2, (y0 + y1) / 2, (FLOOR_TOP + CEIL_BOTTOM) / 2),
                                   unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    assert "/" + CONN + "." in w.get_path_name()
    w.set_editor_property("water_extent", V((x1 - x0) / 2, (y1 - y0) / 2, (CEIL_BOTTOM - FLOOR_TOP) / 2))
    w.set_editor_property("water_volume", True)
    w.set_editor_property("priority", 29)  # Water_Flooded_AtlantisShipwreck is 30 and keeps its -500 surface.
    w.set_editor_property("solid_surface", False)
    w.set_editor_property("underwater_fog_per_metre", 0.06)
    w.set_editor_property("underwater_fog_color", unreal.LinearColor(0.01, 0.07, 0.1, 1))
    tag(w, "Water_Flooded_ShipwreckCavern")
    for i, loc in enumerate(((-8500, -10000, -3400), (-6400, -10400, -3000), (-4500, -10000, -3400))):
        light(loc, "ShipwreckCavern_Light_%d" % i)

    # Report anything else inside the cavern interior (should be only wreck, region and cavern actors).
    allowed_levels = {REGION.rsplit("/", 1)[1]} | {d.rsplit("/", 1)[1] for d in COPIES.values()}
    for a in EAS.get_all_level_actors():
        lv = a.get_level().get_outermost().get_name().rsplit("/", 1)[1]
        if lv in allowed_levels or TAG in [str(t) for t in a.get_editor_property("tags")]:
            continue
        o, e = a.get_actor_bounds(True)
        lo, hi = o - e, o + e
        if e.x > 50000 or e.y > 50000:
            continue
        if lo.x < x1 and hi.x > x0 and lo.y < y1 and hi.y > y0 and lo.z < CEIL_BOTTOM and hi.z > FLOOR_TOP:
            R["intruders"].append({"level": lv, "label": a.get_actor_label(), "class": a.get_class().get_name(),
                                   "min": [round(v) for v in lo.to_tuple()], "max": [round(v) for v in hi.to_tuple()]})

    conn_level = next(a for a in EAS.get_all_level_actors() if "/" + CONN + "." in a.get_path_name()).get_outermost()
    assert unreal.EditorLoadingAndSavingUtils.save_packages([world.get_outermost(), conn_level], False), "save failed"
    R["main_sha256_after"] = sha(MAIN_FILE)
    R["hash_after"] = {str(p): sha(p) for p in guarded}
    assert R["hash_after"] == R["hash_before"], "region map or a vendor sublevel changed"
    R["success"] = True
except Exception:
    R["errors"].append(traceback.format_exc())
    unreal.log_error(R["errors"][-1])
finally:
    (OUT / "index.json").write_text(json.dumps(R, indent=1, default=str))
    print("SHIPWRECK_DEEP_DONE", OUT)
