"""Read-only inventory of connected-world lighting and exposure settings."""
import json
import traceback
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\IndustrialHospital\Atmosphere_Audit.json")
report = {"actors": [], "errors": []}

def properties(obj, names):
    result = {}
    for name in names:
        try:
            value = obj.get_editor_property(name)
            result[name] = value if isinstance(value, (bool, int, float, str)) else str(value)
        except Exception:
            pass
    return result

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(
        "/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
    if not world:
        raise RuntimeError("Connected map did not load")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in eas.get_all_level_actors():
        components = []
        for component in actor.get_components_by_class(unreal.ActorComponent):
            name = component.get_class().get_name()
            if any(word in name for word in ("LightComponent", "FogComponent", "LocalFogVolumeComponent")):
                components.append({"class": name, "name": component.get_name(), **properties(component, (
                    "intensity", "intensity_units", "attenuation_radius", "visible", "light_color",
                    "fog_density", "fog_height_falloff", "fog_inscattering_color",
                    "volumetric_fog", "volumetric_fog_emissive", "radial_fog_extinction",
                    "height_fog_extinction", "fog_emissive", "fog_albedo"))})
        settings = None
        if isinstance(actor, unreal.PostProcessVolume):
            settings = properties(actor.get_editor_property("settings"), (
                "override_auto_exposure_method", "auto_exposure_method",
                "override_auto_exposure_bias", "auto_exposure_bias",
                "override_auto_exposure_min_brightness", "auto_exposure_min_brightness",
                "override_auto_exposure_max_brightness", "auto_exposure_max_brightness",
                "override_bloom_intensity", "bloom_intensity", "bloom_threshold"))
        if components or settings is not None:
            report["actors"].append({"label": actor.get_actor_label(),
                "class": actor.get_class().get_name(), "level": actor.get_level().get_path_name(),
                "location": actor.get_actor_location().to_tuple(),
                "volume": properties(actor, ("unbound", "priority", "blend_weight", "enabled")),
                "components": components, "post_process": settings})
    report["success"] = True
except Exception:
    report["errors"].append(traceback.format_exc())
    report["success"] = False
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("ATMOSPHERE_AUDIT " + str(report["success"]))
