import json
from pathlib import Path
import unreal

OUT = Path(r"F:\Carnival\Saved\IndustrialHospital\Runtime_Asset_Inspection.json")
results = {"classes": {}, "snow_levels": []}
for name in (
    "Emitter", "ParticleSystem", "ParticleSystemComponent", "AudioComponent",
    "AmbientSound", "SoundWave", "SoundFactory", "SoundAttenuation",
    "LocalFogVolume", "LocalFogVolumeComponent", "ExponentialHeightFog", "PostProcessVolume",
):
    value = getattr(unreal, name, None)
    if value:
        results["classes"][name] = {
            "doc": getattr(value, "__doc__", None),
            "members": {member: getattr(getattr(value, member, None), "__doc__", None)
                        for member in dir(value)
                        if any(term in member.lower() for term in
                               ("template", "particle", "sound", "attenuation", "loop", "auto", "radius", "fog", "density", "height", "falloff", "extent", "albedo"))},
        }

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for path in (
    "/Game/Creepwood_Carnival_Meshingun/Environment/Map/Lv_LightingNightSnow",
    "/Game/IndustrialSlums/Levels/L_Night",
):
    world = unreal.EditorLoadingAndSavingUtils.load_map(path)
    entry = {"map": path, "actors": []}
    for actor in eas.get_all_level_actors():
        info = {"class": actor.get_class().get_name(), "label": actor.get_actor_label(),
                "location": actor.get_actor_location().to_tuple()}
        for component_class in (unreal.ParticleSystemComponent, unreal.AudioComponent):
            try:
                components = actor.get_components_by_class(component_class)
                if components:
                    component = components[0]
                    props = {}
                    for key in ("template", "sound", "auto_activate", "auto_destroy", "attenuation_settings"):
                        try:
                            value = component.get_editor_property(key)
                            props[key] = value.get_path_name() if value else None
                        except Exception:
                            pass
                    info["particle" if component_class == unreal.ParticleSystemComponent else "audio"] = props
            except Exception as exc:
                info["component_error"] = repr(exc)
        if info["class"] == "Emitter":
            try:
                comp = actor.get_editor_property("particle_system_component")
                template = comp.get_editor_property("template")
                info["particle_asset"] = template.get_path_name() if template else None
            except Exception as exc:
                info["particle_error"] = repr(exc)
        if info["class"] == "LocalFogVolume":
            try:
                comp = actor.get_editor_property("local_fog_volume_volume")
                info["fog_component"] = {key: repr(comp.get_editor_property(key))
                                          for key in ("fog_density", "fog_height", "fog_distance", "fog_falloff", "albedo", "extinction_scale")
                                          if key in dir(unreal.LocalFogVolumeComponent)}
            except Exception as exc:
                info["fog_error"] = repr(exc)
        if info["class"] in ("Emitter", "ExponentialHeightFog", "LocalFogVolume", "PostProcessVolume",
                             "DirectionalLight", "SkyAtmosphere", "SkyLight", "HDRIBackdrop_C"):
            entry["actors"].append(info)
    results["snow_levels"].append(entry)
    unreal.log(f"INDUSTRIAL_HOSPITAL_RUNTIME_ASSETS {path} actors={len(entry['actors'])}")

OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_HOSPITAL_RUNTIME_ASSET_INSPECTION_SAVED")
