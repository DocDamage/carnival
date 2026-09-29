"""Exercise motorcycle mount, dismount, and rider recovery in map PIE.

Run from the full editor with:
  -ExecutePythonScript=F:/Carnival/Scripts/run_motorcycle_pie_acceptance.py

All spawned blockers and actor repositioning occur in the unsaved PIE world.
Rendered frames are captured from the active game viewport when available.
"""

import json
import math
import time
import traceback
from pathlib import Path

import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


ROOT = Path(r"F:\Carnival")
MAP = "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
OUT = ROOT / "Saved/HauntedDollIntegration/PIE_MotorcycleAnimationContactReview_Readable"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "index.json"
LIVE = OUT / "live.json"

sys_path = str(ROOT / "Scripts")
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
from mansion_route_config import route_manifest


world = unreal.EditorLevelLibrary.get_editor_world()
if not world or world.get_name() != MAP.rsplit("/", 1)[-1]:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError(f"Could not load {MAP}")

editor_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
route = route_manifest()["route_world"]
start = unreal.Vector(*route[0])
next_point = unreal.Vector(*route[1])
forward = unreal.Vector(next_point.x - start.x, next_point.y - start.y, 0.0)
forward_length = math.hypot(forward.x, forward.y)
forward = unreal.Vector(forward.x / max(forward_length, 1.0), forward.y / max(forward_length, 1.0), 0.0)
right = unreal.Vector(-forward.y, forward.x, 0.0)
yaw = math.degrees(math.atan2(forward.y, forward.x))
bike_location = start + unreal.Vector(0.0, 0.0, 4.0)
bike_rotation = unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0)

report = {
    "map": MAP,
    "mode": "rendered editor PIE where supported",
    "route_start": list(start.to_tuple()),
    "checks": [],
    "captures": [],
    "animation_samples": [],
    "errors": [],
}
state = {
    "phase": "setup",
    "busy": False,
    "started": time.monotonic(),
    "deadline": time.monotonic() + 300.0,
    "game": None,
    "player": None,
    "controller": None,
    "bike": None,
    "side_index": 0,
    "sides": [
        {"name": "left", "mount_left": True, "forward_cm": 30.0, "side_cm": -60.0,
         "mount_surface": "flat", "dismount_surface": "flat"},
        {"name": "right", "mount_left": False, "forward_cm": -25.0, "side_cm": 60.0,
         "mount_surface": "cross_slope", "dismount_surface": "cross_slope"},
    ],
    "capture_times": [],
    "capture_index": 0,
    "capture_kind": "",
    "capture_deadline": 0.0,
    "next_sample": 0.0,
    "surface_index": 0,
    "surface_name": "flat",
    "flat_bike_location": None,
    "flat_bike_rotation": None,
    "bike_location": bike_location,
    "bike_rotation": bike_rotation,
    "forward": forward,
    "right": right,
    "dismount_blocker": None,
    "slope_floor": None,
    "next_setup_attempt": 0.0,
    "setup_attempts": 0,
}
blocker_fixture = {}
visual_fixtures = []

# Keep the saved map untouched while giving the live graph capture a readable
# temporary light rig and a collision-backed ten-degree cross-slope pad.
flat_route_index = 9
flat_point = unreal.Vector(*route[flat_route_index])
flat_following = unreal.Vector(*route[flat_route_index + 1])
flat_direction = unreal.Vector(flat_following.x - flat_point.x,
                               flat_following.y - flat_point.y, 0.0)
flat_length = math.hypot(flat_direction.x, flat_direction.y)
flat_direction = unreal.Vector(flat_direction.x / max(flat_length, 1.0),
                               flat_direction.y / max(flat_length, 1.0), 0.0)
flat_heading = math.degrees(math.atan2(flat_direction.y, flat_direction.x))

slope_actor = editor_actors.spawn_actor_from_class(
    unreal.StaticMeshActor,
    flat_point + unreal.Vector(0.0, 0.0, -20.0),
    unreal.Rotator(pitch=0.0, yaw=flat_heading, roll=10.0))
slope_actor.set_actor_label("CarnivalMotorcycleSlopeFixture")
slope_component = slope_actor.get_component_by_class(unreal.StaticMeshComponent)
slope_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
slope_component.set_collision_profile_name("BlockAll")
slope_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
slope_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
slope_actor.set_actor_scale3d(unreal.Vector(20.0, 20.0, 0.4))
visual_fixtures.append(slope_actor)

for fixture_index, (pitch, light_yaw, intensity) in enumerate(((-45.0, -35.0, 30.0), (-30.0, 150.0, 15.0))):
    light_actor = editor_actors.spawn_actor_from_class(
        unreal.DirectionalLight,
        flat_point + unreal.Vector(0.0, 0.0, 500.0),
        unreal.Rotator(pitch=pitch, yaw=light_yaw, roll=0.0))
    light_actor.set_actor_label(f"CarnivalMotorcycleCaptureLight{fixture_index}")
    light_component = light_actor.get_component_by_class(unreal.DirectionalLightComponent)
    light_component.set_editor_property("intensity", intensity)
    light_component.set_editor_property("cast_shadows", False)
    light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    visual_fixtures.append(light_actor)

report["temporary_capture_setup"] = {
    "flat_route_index": flat_route_index,
    "cross_slope_degrees": 10.0,
    "temporary_lights": 2,
    "temporary_light_intensity_lux": [30.0, 15.0],
    "temporary_lights_cast_shadows": False,
    "saved_map_modified": False,
}


def configure_surface(index):
    point = unreal.Vector(*route[index])
    following = unreal.Vector(*route[index + 1])
    direction = unreal.Vector(following.x - point.x, following.y - point.y, 0.0)
    length = math.hypot(direction.x, direction.y)
    direction = unreal.Vector(direction.x / max(length, 1.0), direction.y / max(length, 1.0), 0.0)
    lateral = unreal.Vector(-direction.y, direction.x, 0.0)
    heading = math.degrees(math.atan2(direction.y, direction.x))
    state.update(
        surface_index=index,
        surface_name="flat" if index == 0 else "coastal_grade",
        bike_location=point + unreal.Vector(0.0, 0.0, 4.0),
        bike_rotation=unreal.Rotator(pitch=0.0, yaw=heading, roll=0.0),
        forward=direction,
        right=lateral,
    )
    dz = following.z - point.z
    state["grade_degrees"] = math.degrees(math.atan2(dz, max(length, 1.0)))
    return point


configure_surface(0)


def configure_flat_surface():
    """Use the nearly level, collision-backed route segment by spawn."""
    if state.get("flat_bike_location") is None:
        raise RuntimeError("The PIE player start has not been resolved")
    state.update(
        surface_index=-1,
        surface_name="near_flat_spawn_route",
        bike_location=state["flat_bike_location"],
        bike_rotation=state["flat_bike_rotation"],
        forward=state["flat_forward"],
        right=state["flat_right"],
        grade_degrees=state.get("flat_grade_degrees", 0.0),
    )
    slope_floor = state.get("slope_floor")
    if slope_floor:
        slope_floor.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return state["bike_location"]


def configure_trial_surface(surface_name):
    if surface_name != "cross_slope":
        configure_flat_surface()
        return state["bike_location"]
    if not state.get("flat_bike_location") or not state.get("slope_floor"):
        raise RuntimeError("The temporary ten-degree cross-slope fixture is not available in PIE")
    state.update(
        surface_index=-2,
        surface_name="temporary_cross_slope_10deg",
        bike_location=state["flat_bike_location"],
        bike_rotation=state["flat_bike_rotation"],
        forward=state["flat_forward"],
        right=state["flat_right"],
        grade_degrees=10.0,
    )
    state["slope_floor"].set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    return state["bike_location"]


def mount_approach_location(side):
    bike = state["bike"]
    trigger_prop = "mount_trigger_left" if side["mount_left"] else "mount_trigger_right"
    trigger = bike.get_editor_property(trigger_prop)
    if trigger:
        relative = trigger.get_editor_property("relative_location")
        bike_location = bike.get_actor_location()
        bike_rotation = bike.get_actor_rotation()
        yaw_radians = math.radians(bike_rotation.yaw)
        pitch_radians = math.radians(bike_rotation.pitch)
        roll_radians = math.radians(bike_rotation.roll)
        # The authored triggers are attached to the bike mesh root (unit
        # scale). Rotate their local offsets using the live actor basis.
        local_x, local_y, local_z = relative.x, relative.y, relative.z
        cy, sy = math.cos(yaw_radians), math.sin(yaw_radians)
        cp, sp = math.cos(pitch_radians), math.sin(pitch_radians)
        cr, sr = math.cos(roll_radians), math.sin(roll_radians)
        # Unreal's Rotator order is roll, pitch, yaw (Rz * Ry * Rx).
        rx = cp * cy * local_x + (sr * sp * cy - cr * sy) * local_y + (cr * sp * cy + sr * sy) * local_z
        ry = cp * sy * local_x + (sr * sp * sy + cr * cy) * local_y + (cr * sp * sy - sr * cy) * local_z
        rz = -sp * local_x + sr * cp * local_y + cr * cp * local_z
        seat_z = 98.195294
        seat_world_z = cr * cp * seat_z
        approach_z = bike_location.z + seat_world_z
        if state["surface_name"] == "temporary_cross_slope_10deg":
            # The test slab is rolled about the bike's forward axis. Lift the
            # uphill approach and lower the downhill approach onto that plane.
            lateral_sign = 1.0 if side["mount_left"] is False else -1.0
            approach_z += lateral_sign * math.sin(math.radians(10.0)) * abs(relative.y)
        return unreal.Vector(bike_location.x + rx,
                             bike_location.y + ry,
                             approach_z)
    # Authored component offsets for the C++ defaults; the live components above
    # are preferred so the test follows any Blueprint overrides.
    sign = -1.0 if side["mount_left"] else 1.0
    return state["bike_location"] + state["right"] * (60.0 * sign) + unreal.Vector(0.0, 0.0, 98.195294)


def json_default(value):
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_tuple"):
        return list(value.to_tuple())
    if hasattr(value, "get_path_name"):
        try:
            return value.get_path_name()
        except Exception:
            pass
    return str(value)


def write_live():
    payload = {key: value for key, value in state.items()
               if key not in ("game", "player", "controller", "bike", "busy")}
    LIVE.write_text(json.dumps(payload, indent=2, default=json_default), encoding="utf-8")


def check(name, passed, detail=None):
    entry = {"name": name, "passed": bool(passed)}
    if detail is not None:
        entry["detail"] = detail
    report["checks"].append(entry)
    unreal.log(f"MOTORCYCLE_PIE_CHECK {name} passed={bool(passed)} {detail or ''}")
    write_live()


def collision_name(pawn):
    capsule = pawn.get_component_by_class(unreal.CapsuleComponent)
    if not capsule:
        raise RuntimeError("Player capsule component is missing")
    if not capsule.is_collision_enabled():
        return "NO_COLLISION"
    query = capsule.is_query_collision_enabled()
    physics = capsule.is_physics_collision_enabled()
    if query and physics:
        return "QUERY_AND_PHYSICS"
    if query:
        return "QUERY_ONLY"
    if physics:
        return "PHYSICS_ONLY"
    return "ENABLED_WITHOUT_QUERY_OR_PHYSICS"


def movement_name(pawn):
    movement = pawn.get_component_by_class(unreal.CharacterMovementComponent)
    if not movement:
        raise RuntimeError("Player character-movement component is missing")
    mode = movement.get_editor_property("movement_mode")
    return getattr(mode, "name", str(mode))


def dismounting_flag(bike):
    # Unreal Python strips the native bool's "b" prefix in reflected property
    # names, unlike C++ and generated source. Keep the older spelling as a
    # fallback for engine builds which expose it verbatim.
    for property_name in ("dismounting", "b_dismounting"):
        try:
            return bool(bike.get_editor_property(property_name))
        except Exception:
            pass
    raise RuntimeError("The motorcycle dismounting state is not exposed to Python")


def sample_ground_below(point, player, bike):
    """Measure world floor height below a live animation foot-bone pivot."""
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            state["game"],
            point + unreal.Vector(0.0, 0.0, 30.0),
            point - unreal.Vector(0.0, 0.0, 350.0),
            unreal.TraceTypeQuery.ECC_VISIBILITY,
            False,
            [player, bike],
            unreal.DrawDebugTrace.NONE,
            True,
        )
        hit = hit.to_tuple() if hit else None
        if not hit or not hit[0]:
            return {"hit": False}
        floor_point, normal, actor = hit[5], hit[7], hit[9]
        return {
            "hit": True,
            "floor_z": float(floor_point.z),
            "ankle_pivot_height_cm": float(point.z - floor_point.z),
            "normal_z": float(normal.z),
            "actor": actor.get_actor_label() if actor else None,
        }
    except Exception as error:
        return {"error": str(error)}


def bike_airborne(bike):
    for name in ("is_airborne", "b_is_airborne"):
        try:
            return bool(bike.get_editor_property(name))
        except Exception:
            pass
    return None


def mounted_state(label):
    player, controller, bike = state["player"], state["controller"], state["bike"]
    try:
        current_rider = bike.get_editor_property("current_rider")
    except Exception:
        current_rider = getattr(bike, "current_rider", None)
    try:
        capsule = collision_name(player)
    except Exception as error:
        capsule = f"error:{error}"
    try:
        movement = movement_name(player)
    except Exception as error:
        movement = f"error:{error}"
    possessed = controller.get_controlled_pawn() == bike
    check(f"{label}: rider attached to bike", current_rider == player,
          {"current_rider": str(current_rider), "expected": str(player)})
    check(f"{label}: controller possesses bike", possessed)
    check(f"{label}: rider capsule disabled", "NO_COLLISION" in capsule.upper(), capsule)
    check(f"{label}: rider movement disabled", "NONE" in movement.upper(), movement)


def recovered_state(label, before_location=None):
    player, controller = state["player"], state["controller"]
    try:
        capsule = collision_name(player)
        movement = movement_name(player)
        possessed = controller.get_controlled_pawn() == player
        position = player.get_actor_location()
        distance = None
        if before_location is not None:
            distance = unreal.Vector.distance(before_location, position)
        check(f"{label}: controller possesses rider", possessed)
        check(f"{label}: rider collision restored", "QUERY_AND_PHYSICS" in capsule.upper(), capsule)
        check(f"{label}: rider walking restored", "WALKING" in movement.upper(), movement)
        if before_location is not None:
            check(f"{label}: rider recovered at a finite location",
                  all(math.isfinite(v) for v in position.to_tuple()),
                  {"before": list(before_location.to_tuple()), "after": list(position.to_tuple()), "distance_cm": distance})
    except Exception as error:
        check(f"{label}: recovery state readable", False, str(error))


def sample_graph(kind, side_name):
    player, bike = state["player"], state["bike"]
    try:
        mesh = player.get_component_by_class(unreal.SkeletalMeshComponent)
        if not mesh:
            raise RuntimeError("Rider skeletal mesh component is missing")
        anim = mesh.get_anim_instance()
        if kind == "mount":
            montage_properties = [(side_name, "mount_left_montage" if side_name == "left" else "mount_right_montage")]
        else:
            montage_properties = [("left", "dismount_left_montage"), ("right", "dismount_right_montage")]
        montages = []
        for montage_side, prop in montage_properties:
            montage = player.get_editor_property(prop)
            montage_position = anim.montage_get_position(montage) if montage else -1.0
            montage_playing = bool(montage and anim.montage_is_playing(montage))
            montages.append({"side": montage_side, "name": montage.get_name() if montage else None,
                             "position": float(montage_position), "playing": montage_playing})
        bones = {}
        for bone in ("pelvis", "head", "foot_l", "foot_r"):
            try:
                bones[bone] = list(mesh.get_socket_location(bone).to_tuple())
            except Exception:
                pass
        foot_floor = {
            foot: sample_ground_below(unreal.Vector(*bones[foot]), player, bike)
            for foot in ("foot_l", "foot_r") if foot in bones
        }
        input_state = {}
        for key_name in ("E", "F", "Gamepad_FaceButton_Top"):
            try:
                key = unreal.Key()
                key.import_text(f'(KeyName="{key_name}")')
                input_state[key_name] = {"key": key.export_text()}
            except Exception as error:
                input_state[key_name] = f"unavailable:{error}"
                continue
            try:
                input_state[key_name]["down"] = bool(state["controller"].is_input_key_down(key))
            except Exception as error:
                input_state[key_name]["down_error"] = str(error)
            try:
                input_state[key_name]["time_down"] = float(state["controller"].get_input_key_time_down(key))
            except Exception as error:
                input_state[key_name]["time_down_error"] = str(error)
        try:
            mounted_motorcycle = str(player.get_editor_property("mounted_motorcycle"))
        except Exception as error:
            mounted_motorcycle = f"unavailable:{error}"
        report["animation_samples"].append({
            "kind": kind,
            "side": side_name,
            "game_seconds": round(unreal.GameplayStatics.get_time_seconds(state["game"]), 4),
            "montages": montages,
            "rider_location": list(player.get_actor_location().to_tuple()),
            "bike_location": list(bike.get_actor_location().to_tuple()),
            "surface": state["surface_name"],
            "slope_degrees": state.get("grade_degrees", 0.0),
            "bones_world": bones,
            "foot_floor": foot_floor,
            "current_rider": str(bike.get_editor_property("current_rider")),
            "player_mounted_motorcycle": mounted_motorcycle,
            "controller_pawn": str(state["controller"].get_controlled_pawn()),
            "dismounting": dismounting_flag(bike),
            "input_keys": input_state,
            "rider_collision": collision_name(player),
            "rider_movement": movement_name(player),
            "camera_world": list(bike.get_component_by_class(unreal.CameraComponent)
                                  .get_world_location().to_tuple()),
        })
    except Exception as error:
        report["animation_samples"].append({"kind": kind, "side": side_name, "error": str(error)})


def begin_capture_sequence(kind, side_name, times):
    state["capture_kind"] = f"{kind}_{side_name}"
    state["capture_times"] = list(times)
    state["capture_index"] = 0
    state["sequence_start"] = unreal.GameplayStatics.get_time_seconds(state["game"])
    state["phase"] = "sequence_capture"
    state["next_sample"] = state["sequence_start"]
    boom = state["bike"].get_editor_property("camera_boom")
    if boom:
        side_yaw = 90.0 if side_name == "left" else -90.0
        boom.set_relative_rotation(unreal.Rotator(pitch=-5.0, yaw=side_yaw, roll=0.0), False, True)
    report["animations"] = report.get("animations", [])
    report["animations"].append({
        "kind": kind,
        "side": side_name,
        "start_game_seconds": state["sequence_start"],
        "capture_schedule_seconds": list(times),
    })
    # Save the graph state at Montage_Play time before the first world tick can
    # advance or interrupt the transition.
    sample_graph(kind, side_name)
    write_live()


def issue_capture(kind, side_name, elapsed):
    stamp = int(round(elapsed * 1000.0))
    path = OUT / f"{kind}_{side_name}_{stamp:04d}ms.png"
    if path.exists():
        path.unlink()
    unreal.SystemLibrary.execute_console_command(
        state["game"],
        'HighResShot 1280x800 filename="' + str(path).replace("\\", "/") + '"')
    state["capture_path"] = path
    state["capture_deadline"] = time.monotonic() + 12.0
    state["phase"] = "capture_wait"
    sample_graph(kind, side_name)


def set_approach(side):
    player, bike = state["player"], state["bike"]
    approach = mount_approach_location(side)
    location = approach + state["forward"] * side.get("forward_cm", 15.0)
    player.set_actor_location_and_rotation(location, state["bike_rotation"], False, False)
    return location


def position_pie_blocker(game, location, scale):
    if not blocker_fixture:
        candidates = unreal.GameplayStatics.get_all_actors_of_class(game, unreal.StaticMeshActor)
        for actor in candidates:
            if actor == state["bike"]:
                continue
            components = actor.get_components_by_class(unreal.StaticMeshComponent)
            if not components:
                continue
            component = components[0]
            mesh = component.get_editor_property("static_mesh")
            if not mesh:
                continue
            try:
                original_mobility = component.get_editor_property("mobility")
            except Exception:
                original_mobility = None
            blocker_fixture.update(
                actor=actor,
                component=component,
                location=actor.get_actor_location(),
                rotation=actor.get_actor_rotation(),
                scale=actor.get_actor_scale3d(),
                mesh=mesh,
                collision_profile=component.get_collision_profile_name(),
                mobility=original_mobility,
            )
            try:
                component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            except Exception as mobility_error:
                try:
                    component.set_mobility(unreal.ComponentMobility.MOVABLE)
                except Exception as fallback_error:
                    blocker_fixture.clear()
                    raise RuntimeError(
                        f"Cannot make temporary blocker movable: {mobility_error}; {fallback_error}")
            component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
            component.set_collision_profile_name("BlockAll")
            component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            break
        if not blocker_fixture:
            raise RuntimeError("No PIE static-mesh actor was available for the temporary blocker")
    actor = blocker_fixture["actor"]
    component = blocker_fixture["component"]
    try:
        component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    except Exception as mobility_error:
        try:
            component.set_mobility(unreal.ComponentMobility.MOVABLE)
        except Exception as fallback_error:
            raise RuntimeError(
                f"Cannot reactivate temporary blocker mobility: {mobility_error}; {fallback_error}")
    actor.set_actor_location_and_rotation(location, unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0), False, True)
    actor.set_actor_scale3d(scale)
    actual = actor.get_actor_location()
    if unreal.Vector.distance(actual, location) > 1.0:
        raise RuntimeError(
            f"Temporary blocker did not move (mobility={blocker_fixture.get('mobility')}, "
            f"actual={actual}, requested={location})")
    return actor


def restore_pie_blocker():
    if not blocker_fixture:
        return
    actor = blocker_fixture["actor"]
    component = blocker_fixture["component"]
    component.set_static_mesh(blocker_fixture["mesh"])
    component.set_collision_profile_name(blocker_fixture["collision_profile"])
    actor.set_actor_location_and_rotation(
        blocker_fixture["location"], blocker_fixture["rotation"], False, True)
    actor.set_actor_scale3d(blocker_fixture["scale"])
    if blocker_fixture.get("mobility") is not None:
        try:
            component.set_editor_property("mobility", blocker_fixture["mobility"])
        except Exception:
            pass


def pie_blocker_details():
    if not blocker_fixture:
        return None
    actor = blocker_fixture["actor"]
    component = blocker_fixture["component"]
    details = {
        "actor": actor.get_name(),
        "location": list(actor.get_actor_location().to_tuple()),
        "scale": list(actor.get_actor_scale3d().to_tuple()),
        "collision_profile": str(component.get_collision_profile_name()),
    }
    try:
        details["mobility"] = str(component.get_editor_property("mobility"))
    except Exception as error:
        details["mobility"] = f"unavailable:{error}"
    return details


def begin_mount_for_side(index):
    side = state["sides"][index]
    player, controller, bike = state["player"], state["controller"], state["bike"]
    # One side starts on the nearly level road pad and the other on the
    # temporary cross-slope fixture so both fitted mount clips are exercised.
    configure_trial_surface(side["mount_surface"])
    if controller.get_controlled_pawn() != player:
        controller.possess(player)
    bike.set_actor_location_and_rotation(state["bike_location"], state["bike_rotation"], False, True)
    bike.input_throttle(0.0)
    bike.input_steering(0.0)
    bike.input_brake(1.0)
    approach = mount_approach_location(side)
    start = approach + state["forward"] * side.get("forward_cm", 15.0)
    player.set_actor_location_and_rotation(start, state["bike_rotation"], False, True)
    state["side_index"] = index
    state["pending_mount"] = {
        "side": side["name"], "approach": approach, "start": start,
    }
    # Give the actor/component transforms and floor support one game tick to
    # settle after teleporting before asking CanMount/AlignRiderForMount.
    state["phase"] = "mount_attempt"


def attempt_mount_for_side(index):
    side = state["sides"][index]
    player, controller, bike = state["player"], state["controller"], state["bike"]
    approach = mount_approach_location(side)
    offset = side["forward_cm"]
    attempts = []
    mounted = False
    # Keep the rider on the requested side while reducing the walk-up length
    # if a world prop clips the longer capsule sweep. A non-zero offset is
    # required for the acceptance check; the zero offset is diagnostic only
    # and lets the live animation pass continue if the pad is obstructed.
    for multiplier in (1.0, 0.5, 0.25, 0.0):
        offset = side["forward_cm"] * multiplier
        player_location = approach + state["forward"] * offset
        player.set_actor_location_and_rotation(player_location, state["bike_rotation"], False, True)
        try:
            can_mount_result = str(bike.can_mount(player))
        except Exception as error:
            can_mount_result = f"unavailable:{error}"
        bike.mount(player, side["mount_left"])
        mounted = (bike.get_editor_property("current_rider") == player
                   and controller.get_controlled_pawn() == bike)
        attempts.append({
            "forward_offset_cm": offset,
            "player_location": list(player_location.to_tuple()),
            "can_mount_api": can_mount_result,
            "mounted": mounted,
        })
        if mounted:
            break
    mounted = (bike.get_editor_property("current_rider") == player
               and controller.get_controlled_pawn() == bike)
    diagnostics = {
        "attempts": attempts,
        "accepted_offset_cm": offset if mounted else None,
        "approach_location": list(approach.to_tuple()),
        "bike_location": list(bike.get_actor_location().to_tuple()),
        "bike_rotation": str(bike.get_actor_rotation()),
        "bike_airborne": bike_airborne(bike),
        "bike_speed": float(bike.get_editor_property("current_speed")),
    }
    offset_accepted = mounted and abs(offset) > 0.1
    check(f"{side['name']} offset mount accepted", offset_accepted, diagnostics)
    if not mounted:
        state["mount_attempt_failed"] = True
        state["phase"] = "mount_right" if index == 0 else "controller_loss_mount"
        return
    state["mount_attempt_failed"] = not offset_accepted
    mounted_state(f"{side['name']} mount")
    montage_playing = False
    montage_name = None
    try:
        mesh = player.get_component_by_class(unreal.SkeletalMeshComponent)
        anim = mesh.get_anim_instance()
        montage = player.get_editor_property(
            "mount_left_montage" if side["mount_left"] else "mount_right_montage")
        montage_name = montage.get_name() if montage else None
        montage_playing = bool(montage and anim.montage_is_playing(montage))
    except Exception as error:
        montage_name = f"read_error:{error}"
    check(f"{side['name']} mount montage started", montage_playing,
          {"montage": montage_name, "surface": state["surface_name"]})
    if not montage_playing:
        state["mount_attempt_failed"] = True
        state["phase"] = "mount_right" if index == 0 else "controller_loss_mount"
        return
    begin_capture_sequence("mount", side["name"], (0.10, 0.25, 0.50, 0.80, 1.10, 1.35))


def prepare_fixture_mount(index):
    side = state["sides"][index]
    player, controller, bike = state["player"], state["controller"], state["bike"]
    configure_flat_surface()
    if controller.get_controlled_pawn() != player:
        controller.possess(player)
    bike.set_actor_location_and_rotation(state["bike_location"], state["bike_rotation"], False, True)
    bike.input_throttle(0.0)
    bike.input_steering(0.0)
    bike.input_brake(1.0)
    player.set_actor_location_and_rotation(mount_approach_location(side), state["bike_rotation"], False, True)


def attempt_fixture_mount(label, index):
    side = state["sides"][index]
    player, controller, bike = state["player"], state["controller"], state["bike"]
    try:
        can_mount_result = str(bike.can_mount(player))
    except Exception as error:
        can_mount_result = f"unavailable:{error}"
    bike.mount(player, side["mount_left"])
    mounted = (bike.get_editor_property("current_rider") == player
               and controller.get_controlled_pawn() == bike)
    check(f"{label} fixture mounted", mounted, {
        "can_mount_api": can_mount_result,
        "player_location": list(player.get_actor_location().to_tuple()),
        "approach_location": list(mount_approach_location(side).to_tuple()),
        "bike_location": list(bike.get_actor_location().to_tuple()),
        "bike_airborne": bike_airborne(bike),
        "bike_speed": float(bike.get_editor_property("current_speed")),
    })
    return mounted


def begin_dismount_for_side(index):
    side = state["sides"][index]
    bike = state["bike"]
    player = state["player"]
    if bike.get_editor_property("current_rider") != player:
        check(f"{side['name']} dismount montage started", False,
              "Skipped because the expected rider is not mounted")
        state["movement_start"] = player.get_actor_location()
        state["movement_deadline"] = unreal.GameplayStatics.get_time_seconds(state["game"]) + 0.5
        state["phase"] = "movement_check"
        return
    attempt_dismount_for_side(index)


def attempt_dismount_for_side(index):
    side = state["sides"][index]
    bike = state["bike"]
    player = state["player"]
    configure_trial_surface(side["dismount_surface"])
    bike.set_actor_location_and_rotation(state["bike_location"], state["bike_rotation"], False, True)
    # Keep the obstruction to a narrow post at the preferred left landing so
    # the rider still has room to complete the alternate right-side exit.
    if index == 1:
        left_exit = bike.get_actor_location() - state["right"] * 120.0 + unreal.Vector(0.0, 0.0, 100.0)
        position_pie_blocker(state["game"], left_exit, unreal.Vector(0.05, 0.05, 2.2))
        state["dismount_blocker"] = True
    bike.input_brake(1.0)
    bike.dismount()
    state["dismount_started"] = unreal.GameplayStatics.get_time_seconds(state["game"])
    try:
        started = dismounting_flag(bike)
    except Exception:
        started = False
    active_side = None
    try:
        mesh = player.get_component_by_class(unreal.SkeletalMeshComponent)
        anim = mesh.get_anim_instance()
        for candidate, prop in (("left", "dismount_left_montage"), ("right", "dismount_right_montage")):
            montage = player.get_editor_property(prop)
            if montage and anim.montage_is_playing(montage):
                active_side = candidate
                break
    except Exception:
        pass
    check(f"{active_side or side['name']} dismount montage started", started and active_side is not None,
          {"mount_side": side["name"], "active_side": active_side,
           "rider": str(bike.get_editor_property("current_rider")),
           "surface": state["surface_name"], "slope_degrees": state.get("grade_degrees", 0.0)})
    if not (started and active_side is not None):
        blocker = state.get("dismount_blocker")
        if blocker:
            restore_pie_blocker()
            state["dismount_blocker"] = None
        state["movement_start"] = player.get_actor_location()
        state["movement_deadline"] = unreal.GameplayStatics.get_time_seconds(state["game"]) + 0.5
        state["phase"] = "controller_loss_mount" if index == 1 else "movement_check"
        return
    begin_capture_sequence("dismount", active_side, (0.10, 0.25, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40))


def finish_editor():
    if state.get("finished"):
        return
    state["finished"] = True
    if state.get("controller_input_suppressed") is True and state.get("controller"):
        try:
            state["controller"].enable_input(state["controller"])
        except Exception:
            pass
    report["success"] = bool(report["checks"]) and not report["errors"] and all(check["passed"] for check in report["checks"])
    report["elapsed_seconds"] = round(time.monotonic() - state["started"], 2)
    report["capture_count"] = len([item for item in report["captures"] if item.get("exists")])
    required_playbacks = (("mount", "left"), ("mount", "right"),
                          ("dismount", "left"), ("dismount", "right"))
    actual_playback = all(any(item["name"] == f"{side} {kind} montage started" and item["passed"]
                              for item in report["checks"])
                          for kind, side in required_playbacks)
    report["visual_capture_complete"] = actual_playback and all(
        sum(1 for item in report["captures"]
            if Path(item["path"]).name.startswith(f"{kind}_{side}_") and item.get("exists")) >= 3
        for kind, side in required_playbacks)
    contact_summary = []
    for kind, side in required_playbacks:
        samples = [sample for sample in report["animation_samples"]
                   if sample.get("kind") == kind and sample.get("side") == side]
        if not samples:
            continue
        start_time = next((animation["start_game_seconds"] for animation in report.get("animations", [])
                           if animation["kind"] == kind and animation["side"] == side), None)
        if start_time is not None:
            samples = [sample for sample in samples if sample.get("game_seconds", start_time) - start_time >= 1.20]
        feet = []
        for sample in samples:
            for foot, reading in sample.get("foot_floor", {}).items():
                if reading.get("hit"):
                    feet.append({"foot": foot, "ankle_pivot_height_cm": reading["ankle_pivot_height_cm"],
                                 "floor_actor": reading.get("actor"), "normal_z": reading.get("normal_z")})
        if feet:
            contact_summary.append({
                "kind": kind,
                "side": side,
                "window": "last 0.3 seconds of recorded live graph samples",
                "sample_count": len(feet),
                "ankle_pivot_height_cm_min": min(item["ankle_pivot_height_cm"] for item in feet),
                "ankle_pivot_height_cm_max": max(item["ankle_pivot_height_cm"] for item in feet),
                "surface_actors": sorted({item["floor_actor"] for item in feet if item["floor_actor"]}),
            })
    report["foot_floor_contact_summary"] = contact_summary
    report["success"] = report["success"] and report["visual_capture_complete"]
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_live()
    try:
        unreal.unregister_slate_post_tick_callback(handle)
    except Exception:
        pass
    try:
        level_editor.editor_request_end_play()
    except Exception:
        pass
    for fixture in visual_fixtures:
        try:
            editor_actors.destroy_actor(fixture)
        except Exception:
            pass
    unreal.log(f"MOTORCYCLE_PIE_FINISHED success={report['success']} checks={len(report['checks'])} errors={len(report['errors'])}")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def finish_with_error(error):
    report["errors"].append(str(error))
    report["traceback"] = traceback.format_exc()
    state["phase"] = "finish"
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_live()
    finish_editor()


def tick(delta):
    if state["busy"] or state.get("finished"):
        return
    state["busy"] = True
    try:
        if time.monotonic() > state["deadline"]:
            finish_with_error(f"Timed out in phase {state['phase']}")
            return

        if state["phase"] == "finish":
            finish_editor()
            return

        game = unreal.EditorLevelLibrary.get_game_world()
        if state["phase"] in ("setup", "setup_wait"):
            if time.monotonic() < state["next_setup_attempt"]:
                return
            state["next_setup_attempt"] = time.monotonic() + 0.5
            state["setup_attempts"] += 1
            if not game:
                if state["phase"] == "setup":
                    unreal.log("MOTORCYCLE_PIE requesting PIE")
                    level_editor.editor_request_begin_play()
                    state["phase"] = "wait_pie"
                    state["deadline"] = time.monotonic() + 120.0
                write_live()
                return
            state["game"] = game
            if not state.get("slope_floor"):
                slope_actors = [actor for actor in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.StaticMeshActor)
                                if "CarnivalMotorcycleSlopeFixture" in actor.get_actor_label()]
                if not slope_actors:
                    raise RuntimeError("The temporary cross-slope actor was not copied into PIE")
                state["slope_floor"] = slope_actors[0].get_component_by_class(unreal.StaticMeshComponent)
                state["slope_floor"].set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            player = unreal.GameplayStatics.get_player_pawn(game, 0)
            if not player:
                state["phase"] = "setup_wait"
                report.setdefault("setup_observations", []).append({
                    "attempt": state["setup_attempts"], "game": game.get_name(), "player": None})
                write_live()
                return
            bikes = list(unreal.GameplayStatics.get_all_actors_of_class(game, unreal.CarnivalMotorcycle))
            if not bikes:
                state["phase"] = "setup_wait"
                report.setdefault("setup_observations", []).append({
                    "attempt": state["setup_attempts"], "game": game.get_name(),
                    "player": player.get_class().get_name(), "bike_count": 0})
                write_live()
                return
            state["player"] = player
            state["controller"] = unreal.GameplayStatics.get_player_controller(game, 0)
            unreal.SystemLibrary.execute_console_command(game, 'ShowFlag.HUD 0')
            report['capture_hud'] = 'hidden for transition frames only'
            state["bike"] = bikes[0]
            report["player_class"] = player.get_class().get_name()
            report["bike_class"] = state["bike"].get_class().get_name()
            report["bike_count"] = len(bikes)
            report["controller_input_api"] = [name for name in dir(state["controller"])
                                                if "input" in name.lower() or "key" in name.lower()]
            report["controller_unpossess_api"] = [name for name in dir(state["controller"])
                                                    if "unpossess" in name.lower()]
            try:
                state["controller"].disable_input(state["controller"])
                state["controller_input_suppressed"] = True
            except Exception as error:
                state["controller_input_suppressed"] = f"unavailable:{error}"
            report["controller_input_suppressed"] = state["controller_input_suppressed"]
            try:
                state["controller"].set_control_rotation(unreal.Rotator(
                    pitch=-12.0, yaw=state["bike_rotation"].yaw, roll=0.0))
                camera_boom = state["bike"].get_editor_property("camera_boom")
                if camera_boom:
                    camera_boom.set_editor_property("do_collision_test", False)
                    camera_boom.set_editor_property("target_arm_length", 360.0)
                    camera_boom.set_editor_property("use_pawn_control_rotation", False)
                    camera_boom.set_relative_location(unreal.Vector(0.0, 0.0, 105.0), False, True)
                camera = state["bike"].get_component_by_class(unreal.CameraComponent)
                if camera:
                    settings = camera.get_editor_property("post_process_settings")
                    for name, value in {
                        "override_auto_exposure_method": True,
                        "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
                        "override_auto_exposure_bias": True,
                        "auto_exposure_bias": -2.5,
                        "override_auto_exposure_apply_physical_camera_exposure": True,
                        "auto_exposure_apply_physical_camera_exposure": False,
                    }.items():
                        settings.set_editor_property(name, value)
                    camera.set_editor_property("post_process_settings", settings)
                    camera.set_editor_property("post_process_blend_weight", 1.0)
                report["capture_camera_setup"] = "side-on live bike camera; manual exposure; low-intensity shadow-free temporary fill lights in PIE"
            except Exception as error:
                report["capture_camera_setup"] = f"default camera retained: {error}"
            try:
                controller_input = state["controller"].get_editor_property("input_component")
                report["controller_input_component"] = str(controller_input)
                if controller_input:
                    report["controller_input_component_api"] = [name for name in dir(controller_input)
                                                                 if "block" in name.lower() or "input" in name.lower()]
            except Exception as error:
                report["controller_input_component"] = f"unavailable:{error}"
            player_starts = list(unreal.GameplayStatics.get_all_actors_of_class(game, unreal.PlayerStart))
            if not player_starts:
                raise RuntimeError("No PlayerStart actor is available for the level-ground motorcycle trial")
            player_start = player_starts[0]
            player_start_location = player_start.get_actor_location()
            player_start_rotation = player_start.get_actor_rotation()
            flat_route_point = unreal.Vector(*route[flat_route_index])
            flat_following = unreal.Vector(*route[flat_route_index + 1])
            flat_direction = unreal.Vector(flat_following.x - flat_route_point.x,
                                           flat_following.y - flat_route_point.y, 0.0)
            flat_length = math.hypot(flat_direction.x, flat_direction.y)
            flat_direction = unreal.Vector(flat_direction.x / max(flat_length, 1.0),
                                           flat_direction.y / max(flat_length, 1.0), 0.0)
            flat_lateral = unreal.Vector(-flat_direction.y, flat_direction.x, 0.0)
            flat_heading = math.degrees(math.atan2(flat_direction.y, flat_direction.x))
            state["flat_forward"] = flat_direction
            state["flat_right"] = flat_lateral
            # Route point 9 is the nearly level, collision-backed pavement
            # beside spawn. Keep the rider capsule 4 cm above its waypoint datum.
            state["flat_bike_location"] = flat_route_point + unreal.Vector(0.0, 0.0, 2.2)
            state["flat_bike_rotation"] = unreal.Rotator(
                pitch=0.0, yaw=flat_heading, roll=0.0)
            state["flat_grade_degrees"] = math.degrees(math.atan2(
                flat_following.z - flat_route_point.z, max(flat_length, 1.0)))
            report["player_start"] = {
                "location": list(player_start_location.to_tuple()),
                "rotation": str(player_start_rotation),
                "flat_bike_location": list(state["flat_bike_location"].to_tuple()),
                "flat_route_index": flat_route_index,
                "flat_route_grade_degrees": state["flat_grade_degrees"],
            }
            spawners = list(unreal.GameplayStatics.get_all_actors_of_class(game, unreal.Actor))
            removed = []
            for actor in spawners:
                if actor and actor.get_class().get_name() == "MetaHumanMassSpawner":
                    removed.append(actor.get_actor_label())
                    actor.destroy_actor()
            report["excluded_mass_spawners_in_pie"] = removed
            unreal.GameplayStatics.set_global_time_dilation(game, 1.0)
            state["phase"] = "flat_recovery_setup"
            write_live()
            return

        if state["phase"] == "wait_pie":
            if game:
                state["phase"] = "setup"
                state["deadline"] = time.monotonic() + 300.0
                write_live()
            return

        if not game:
            return
        state["game"] = game
        player, controller, bike = state["player"], state["controller"], state["bike"]
        now = unreal.GameplayStatics.get_time_seconds(game)

        if state["phase"] == "flat_recovery_setup":
            controller.possess(player)
            bike.set_actor_location(state["bike_location"], False, True)
            bike.set_actor_rotation(unreal.Rotator(
                pitch=90.0, yaw=state["bike_rotation"].yaw, roll=0.0), True)
            player.set_actor_location_and_rotation(
                state["bike_location"] - state["right"] * 180.0 + unreal.Vector(0.0, 0.0, 98.195294),
                state["bike_rotation"], False, False)
            before_up = bike.get_actor_up_vector().z
            recoverable = bike.can_recover_from_stuck_or_overturned()
            recovered = bike.try_recover_from_stuck_or_overturned()
            after_up = bike.get_actor_up_vector().z
            check("on-foot overturned bike exposes an actionable recovery state", recoverable, {
                "up_before": before_up, "can_recover": recoverable,
            })
            check("on-foot overturned-bike recovery reports success", recovered,
                  {"up_before": before_up, "up_after": after_up})
            check("on-foot overturned-bike recovery rights bike", after_up > 0.95, after_up)
            check("on-foot recovery keeps player walking", controller.get_controlled_pawn() == player
                  and "WALKING" in movement_name(player).upper())
            state["phase"] = "stuck_recovery_setup"
            return

        if state["phase"] == "stuck_recovery_setup":
            configure_flat_surface()
            side = state["sides"][0]
            controller.possess(player)
            bike.set_actor_location_and_rotation(state["bike_location"], state["bike_rotation"], False, True)
            bike.input_throttle(0.0)
            bike.input_brake(1.0)
            approach = mount_approach_location(side)
            player.set_actor_location_and_rotation(
                approach + state["forward"] * side["forward_cm"], state["bike_rotation"], False, True)
            bike.mount(player, side["mount_left"])
            mounted = (bike.get_editor_property("current_rider") == player
                       and controller.get_controlled_pawn() == bike)
            check("stuck-recovery fixture mounts the player", mounted, {
                "rider": str(bike.get_editor_property("current_rider")),
                "controller_pawn": str(controller.get_controlled_pawn()),
            })
            if not mounted:
                state["phase"] = "out_of_range_left"
                return
            blocker_location = bike.get_actor_location() + state["forward"] * 75.0 + unreal.Vector(0.0, 0.0, 75.0)
            position_pie_blocker(game, blocker_location, unreal.Vector(0.5, 0.5, 1.2))
            state["stuck_blocker_location"] = blocker_location
            state["wait_until"] = now + 1.65
            state["phase"] = "stuck_mount_settle"
            return

        if state["phase"] == "stuck_mount_settle":
            if now < state["wait_until"]:
                return
            bike.input_brake(0.0)
            bike.input_throttle(1.0)
            state["wait_until"] = now + 2.0
            state["phase"] = "stuck_drive_wait"
            return

        if state["phase"] == "stuck_drive_wait":
            if now < state["wait_until"]:
                return
            bike.input_throttle(0.0)
            stuck_ready = bike.can_recover_from_stuck_or_overturned()
            check("blocked throttle reaches the in-game stuck-recovery threshold", stuck_ready, {
                "bike_location": list(bike.get_actor_location().to_tuple()),
                "blocker_location": list(state["stuck_blocker_location"].to_tuple()),
                "speed": float(bike.get_editor_property("current_speed")),
                "up_dot": float(bike.get_actor_up_vector().z),
                "controller_pawn": str(controller.get_controlled_pawn()),
            })
            state["stuck_recovery_before"] = bike.get_actor_location()
            # This is the same mounted gameplay action called by F / Triangle:
            # ACarnivalPlayerController::OnInteractMount delegates to Dismount.
            bike.dismount()
            state["wait_until"] = now + 0.25
            state["phase"] = "stuck_recovery_check"
            return

        if state["phase"] == "stuck_recovery_check":
            if now < state["wait_until"]:
                return
            current_rider = bike.get_editor_property("current_rider")
            state_after = {
                "rider_kept_mounted": current_rider == player,
                "controller_kept_on_bike": controller.get_controlled_pawn() == bike,
                "rider_collision": collision_name(player),
                "rider_movement": movement_name(player),
                "recovery_threshold_cleared": not bike.can_recover_from_stuck_or_overturned(),
                "location_before": list(state["stuck_recovery_before"].to_tuple()),
                "location_after": list(bike.get_actor_location().to_tuple()),
            }
            check("mounted F/Triangle action recovers the stuck motorcycle", bool(
                current_rider == player and controller.get_controlled_pawn() == bike
                and "NO_COLLISION" in state_after["rider_collision"].upper()
                and "NONE" in state_after["rider_movement"].upper()
                and state_after["recovery_threshold_cleared"]), state_after)
            restore_pie_blocker()
            bike.input_throttle(1.0)
            state["stuck_resume_before"] = bike.get_actor_location()
            state["wait_until"] = now + 0.35
            state["phase"] = "stuck_resumption_check"
            return

        if state["phase"] == "stuck_resumption_check":
            if now < state["wait_until"]:
                return
            resumed = (float(bike.get_editor_property("current_speed")) > 0.0
                       and unreal.Vector.distance(state["stuck_resume_before"], bike.get_actor_location()) > 1.0
                       and bike.get_editor_property("current_rider") == player
                       and controller.get_controlled_pawn() == bike)
            check("motorcycle driving resumes after stuck recovery", resumed, {
                "speed": float(bike.get_editor_property("current_speed")),
                "distance_cm": unreal.Vector.distance(state["stuck_resume_before"], bike.get_actor_location()),
                "controller_pawn": str(controller.get_controlled_pawn()),
            })
            bike.input_throttle(0.0)
            bike.input_brake(1.0)
            state["wait_until"] = now + 0.45
            state["phase"] = "stuck_normal_dismount"
            return

        if state["phase"] == "stuck_normal_dismount":
            if now < state["wait_until"]:
                return
            bike.dismount()
            state["wait_until"] = now + 2.0
            state["phase"] = "stuck_normal_dismount_check"
            return

        if state["phase"] == "stuck_normal_dismount_check":
            if now < state["wait_until"] and bike.get_editor_property("current_rider") is not None:
                return
            recovered_state("post-stuck normal dismount")
            check("normal dismount remains available after recovery",
                  bike.get_editor_property("current_rider") is None
                  and controller.get_controlled_pawn() == player
                  and "QUERY_AND_PHYSICS" in collision_name(player).upper()
                  and "WALKING" in movement_name(player).upper(), {
                      "rider": str(bike.get_editor_property("current_rider")),
                      "controller_pawn": str(controller.get_controlled_pawn()),
                      "rider_collision": collision_name(player),
                      "rider_movement": movement_name(player),
                  })
            state["phase"] = "out_of_range_left"
            return

        if state["phase"].startswith("out_of_range_"):
            side_name = state["phase"].replace("out_of_range_", "")
            side = next(entry for entry in state["sides"] if entry["name"] == side_name)
            configure_flat_surface()
            controller.possess(player)
            bike.set_actor_location(state["bike_location"], False, True)
            bike.set_actor_rotation(state["bike_rotation"], False)
            player_location = state["bike_location"] + state["forward"] * 300.0 + state["right"] * side["side_cm"] + unreal.Vector(0.0, 0.0, 98.195294)
            player.set_actor_location_and_rotation(player_location, state["bike_rotation"], False, False)
            bike.mount(player, side["mount_left"])
            check(f"{side_name} out-of-range mount rejected", bike.get_editor_property("current_rider") is None
                  and controller.get_controlled_pawn() == player and "QUERY_AND_PHYSICS" in collision_name(player).upper())
            state["phase"] = "out_of_range_right" if side_name == "left" else "blocked_endpoint"
            return

        if state["phase"] == "blocked_endpoint":
            configure_flat_surface()
            controller.possess(player)
            bike.set_actor_location_and_rotation(state["bike_location"], state["bike_rotation"], False, True)
            side = state["sides"][0]
            endpoint = mount_approach_location(side)
            player.set_actor_location_and_rotation(endpoint, state["bike_rotation"], False, False)
            position_pie_blocker(game, endpoint, unreal.Vector(0.5, 0.5, 1.2))
            state["blocked_endpoint"] = endpoint
            state["phase"] = "blocked_endpoint_attempt"
            return

        if state["phase"] == "blocked_endpoint_attempt":
            side = state["sides"][0]
            try:
                can_mount_result = str(bike.can_mount(player))
            except Exception as error:
                can_mount_result = f"unavailable:{error}"
            bike.mount(player, side["mount_left"])
            endpoint_rejected = (bike.get_editor_property("current_rider") is None
                                 and controller.get_controlled_pawn() == player)
            check("blocked mount endpoint rejects mount", endpoint_rejected, {
                "can_mount_api": can_mount_result,
                "blocker": pie_blocker_details(),
                "current_rider": str(bike.get_editor_property("current_rider")),
                "controller_pawn": str(controller.get_controlled_pawn()),
            })
            restore_pie_blocker()
            if not endpoint_rejected:
                controller.possess(player)
                state["phase"] = "blocked_endpoint_cleanup"
                state["wait_until"] = now + 0.25
                return
            state["phase"] = "blocked_path_setup"
            return

        if state["phase"] == "blocked_endpoint_cleanup":
            if now < state["wait_until"]:
                return
            recovered_state("blocked-endpoint cleanup")
            state["phase"] = "blocked_path_setup"
            return

        if state["phase"] == "blocked_path_setup":
            side = state["sides"][0]
            configure_flat_surface()
            controller.possess(player)
            bike.set_actor_location_and_rotation(state["bike_location"], state["bike_rotation"], False, True)
            endpoint = mount_approach_location(side)
            player_location = endpoint - state["forward"] * 70.0
            player.set_actor_location_and_rotation(player_location, state["bike_rotation"], False, True)
            position_pie_blocker(game, endpoint - state["forward"] * 35.0,
                                 unreal.Vector(0.1, 0.1, 1.2))
            state["blocked_path_endpoint"] = endpoint
            state["phase"] = "blocked_path_attempt"
            return

        if state["phase"] == "blocked_path_attempt":
            side = state["sides"][0]
            try:
                can_mount_result = str(bike.can_mount(player))
            except Exception as error:
                can_mount_result = f"unavailable:{error}"
            bike.mount(player, side["mount_left"])
            path_rejected = (bike.get_editor_property("current_rider") is None
                             and controller.get_controlled_pawn() == player)
            check("blocked path obstacle rejects mount", path_rejected, {
                "can_mount_api": can_mount_result,
                "blocker": pie_blocker_details(),
                "start": list(player.get_actor_location().to_tuple()),
                "endpoint": list(state["blocked_path_endpoint"].to_tuple()),
                "current_rider": str(bike.get_editor_property("current_rider")),
                "controller_pawn": str(controller.get_controlled_pawn()),
            })
            restore_pie_blocker()
            if not path_rejected:
                controller.possess(player)
                state["phase"] = "blocked_path_cleanup"
                state["wait_until"] = now + 0.25
                return
            state["phase"] = "mount_left"
            return

        if state["phase"] == "blocked_path_cleanup":
            if now < state["wait_until"]:
                return
            recovered_state("blocked-path cleanup")
            state["phase"] = "mount_left"
            return

        if state["phase"] in ("mount_left", "mount_right"):
            begin_mount_for_side(0 if state["phase"] == "mount_left" else 1)
            return

        if state["phase"] == "mount_attempt":
            attempt_mount_for_side(state["side_index"])
            return

        if state["phase"] == "dismount_attempt":
            attempt_dismount_for_side(state["pending_dismount_index"])
            return

        if state["phase"] == "sequence_capture":
            capture_kind, side_name = state["capture_kind"].split("_", 1)
            elapsed = now - state["sequence_start"]
            if state["next_sample"] <= now:
                sample_graph(capture_kind, side_name)
                state["next_sample"] = now + (0.025 if elapsed < 0.2 else 0.10)
            if state["capture_index"] < len(state["capture_times"]) and elapsed >= state["capture_times"][state["capture_index"]]:
                issue_capture(capture_kind, side_name, elapsed)
                return
            if capture_kind == "mount" and elapsed >= 1.45 and state["capture_index"] >= len(state["capture_times"]):
                mounted_state(f"{side_name} mount handoff")
                begin_dismount_for_side(state["side_index"])
                return
            if capture_kind == "dismount" and state["capture_index"] >= len(state["capture_times"]):
                # Give the graph its natural final tick. The bike updates after
                # the animation instance on some rendered PIE frames, so a
                # fixed 1.55 s cutoff can sample the last playing frame first.
                if dismounting_flag(bike) and elapsed < 2.5:
                    return
                check(f"{side_name} dismount stage completed", not dismounting_flag(bike),
                      {"elapsed_seconds": elapsed, "dismounting": dismounting_flag(bike)})
                recovered_state(f"{side_name} dismount")
                blocker = state.get("dismount_blocker")
                if blocker:
                    restore_pie_blocker()
                    state["dismount_blocker"] = None
                state["movement_start"] = player.get_actor_location()
                state["movement_deadline"] = now + 0.5
                state["phase"] = "movement_check"
                return
            return

        if state["phase"] == "capture_wait":
            path = state["capture_path"]
            if path.exists() and path.stat().st_size > 1000:
                report["captures"].append({"path": str(path), "exists": True, "elapsed_seconds": round(now-state["sequence_start"], 4)})
                state["capture_index"] += 1
                state["phase"] = "sequence_capture"
                write_live()
            elif time.monotonic() > state["capture_deadline"]:
                report["captures"].append({"path": str(path), "exists": False, "reason": "capture timeout"})
                state["capture_index"] += 1
                state["phase"] = "sequence_capture"
                write_live()
            return

        if state["phase"] == "movement_check":
            player.add_movement_input(state["forward"], 1.0, True)
            if now >= state["movement_deadline"]:
                distance = unreal.Vector.distance(state["movement_start"], player.get_actor_location())
                check(f"{state['sides'][state['side_index']]['name']} dismount restores on-foot movement", distance > 1.0,
                      {"distance_cm": distance})
                state["side_index"] += 1
                if state["side_index"] < len(state["sides"]):
                    begin_mount_for_side(state["side_index"])
                else:
                    state["phase"] = "controller_loss_mount"
                return

        if state["phase"] == "controller_loss_mount":
            prepare_fixture_mount(0)
            state["phase"] = "controller_loss_mount_attempt"
            return

        if state["phase"] == "controller_loss_mount_attempt":
            if not attempt_fixture_mount("controller-loss", 0):
                state["phase"] = "destruction_mount"
                return
            state["phase"] = "controller_loss_wait"
            # Let the fitted step-over finish before detaching controller ownership.
            state["wait_until"] = now + 1.65
            return

        if state["phase"] == "controller_loss_wait":
            if now < state["wait_until"]:
                return
            state["recovery_before"] = player.get_actor_location()
            try:
                controller.k2_unpossess()
                state["controller_loss_method"] = "K2_UnPossess (controller temporarily has no pawn)"
            except Exception as error:
                # Retain a live fallback for engine builds where K2_UnPossess
                # is not Python-bound; the bike still loses controller ownership.
                controller.possess(player)
                state["controller_loss_method"] = f"possess rider handoff; K2_UnPossess unavailable: {error}"
            state["phase"] = "controller_loss_recovery"
            state["wait_until"] = now + 0.35
            return

        if state["phase"] == "controller_loss_recovery":
            if now < state["wait_until"]:
                return
            recovered_state("unexpected controller loss", state["recovery_before"])
            check("unexpected controller loss method exercised", bool(state.get("controller_loss_method")),
                  state.get("controller_loss_method"))
            state["phase"] = "destruction_mount"
            return

        if state["phase"] == "destruction_mount":
            prepare_fixture_mount(1)
            state["phase"] = "destruction_mount_attempt"
            return

        if state["phase"] == "destruction_mount_attempt":
            if not attempt_fixture_mount("destruction", 1):
                state["phase"] = "finish"
                return
            state["phase"] = "destruction_recovery"
            state["wait_until"] = now + 0.25
            state["recovery_before"] = player.get_actor_location()
            return

        if state["phase"] == "destruction_recovery":
            if now < state["wait_until"]:
                return
            bike.destroy_actor()
            state["bike"] = None
            state["phase"] = "destruction_recovery_check"
            state["wait_until"] = now + 0.25
            return

        if state["phase"] == "destruction_recovery_check":
            if now < state["wait_until"]:
                return
            recovered_state("bike destruction", state["recovery_before"])
            state["phase"] = "finish"
            report["success"] = all(item["passed"] for item in report["checks"])
            REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
            write_live()
            finish_editor()
            return

    except Exception as error:
        finish_with_error(error)
    finally:
        state["busy"] = False


REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
LIVE.write_text(json.dumps({"phase": "waiting_for_pie"}), encoding="utf-8")
handle = unreal.register_slate_post_tick_callback(tick)

