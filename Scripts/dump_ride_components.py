"""Dump component hierarchies for Creepwood ride Blueprint actors in the loaded level.

For each actor whose class name contains "Ride", record every component's name,
class, mobility, relative location and attach parent, and write a JSON report to
<Saved>/CarnivalKit/RideComponents.json. This is the input for choosing the
motion source and placing seat anchors without opening each Blueprint by hand.
"""
import json
import os

import unreal


def _subsys():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _scene_info(comp):
    info = {"class": comp.get_class().get_name()}
    try:
        loc = comp.get_relative_location()
        info["rel_loc"] = [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)]
    except Exception:
        pass
    try:
        rot = comp.get_relative_rotation()
        info["rel_rot"] = [round(rot.roll, 2), round(rot.pitch, 2), round(rot.yaw, 2)]
    except Exception:
        pass
    try:
        info["mobility"] = str(comp.mobility)
    except Exception:
        pass
    try:
        parent = comp.get_attach_parent()
        info["parent"] = parent.get_name() if parent else None
    except Exception:
        pass
    return info


def _component_info(comp):
    info = {"name": comp.get_name(), "class": comp.get_class().get_name()}
    try:
        if isinstance(comp, unreal.SceneComponent):
            info.update(_scene_info(comp))
    except Exception:
        pass
    return info


def main():
    actors = _subsys().get_all_level_actors()
    rides = []
    for actor in actors:
        cls = actor.get_class().get_name()
        if "ride" not in cls.lower():
            continue
        comps = actor.get_components_by_class(unreal.ActorComponent)
        rides.append({
            "label": actor.get_actor_label(),
            "class": cls,
            "object_path": actor.get_path_name(),
            "location": [round(v, 2) for v in [actor.get_actor_location().x,
                                               actor.get_actor_location().y,
                                               actor.get_actor_location().z]],
            "components": [_component_info(c) for c in comps if c is not None],
        })

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "CarnivalKit")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "RideComponents.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"count": len(rides), "rides": rides}, f, indent=2)
    unreal.log_warning("CarnivalKit: dumped %d ride component hierarchies to %s" % (len(rides), out_path))


main()
