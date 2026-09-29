"""Inspect sky material values and isolate its contribution in an unsaved world."""
import json
import runpy
from pathlib import Path
import unreal

sky_actors = []

def setup(world, eas):
    records = []
    for actor in eas.get_all_level_actors():
        if "sky" not in (actor.get_actor_label() + actor.get_class().get_name()).lower():
            continue
        record = {"label": actor.get_actor_label(), "class": actor.get_class().get_name(),
                  "level": actor.get_level().get_path_name(),
                  "location": actor.get_actor_location().to_tuple(),
                  "scale": actor.get_actor_scale3d().to_tuple(), "meshes": []}
        origin, extent = actor.get_actor_bounds(False, True)
        record["bounds"] = {"origin": origin.to_tuple(), "extent": extent.to_tuple()}
        for component in actor.get_components_by_class(unreal.SkyAtmosphereComponent):
            record["atmosphere"] = {}
            for name in ("sky_luminance_factor", "sky_and_aerial_perspective_luminance_factor",
                         "multi_scattering_factor", "rayleigh_scattering_scale", "mie_scattering_scale"):
                record["atmosphere"][name] = str(component.get_editor_property(name))
        meshes = actor.get_components_by_class(unreal.StaticMeshComponent)
        if meshes:
            sky_actors.append(actor)
        for mesh in meshes:
            item = {"mesh": str(mesh.get_editor_property("static_mesh")), "materials": []}
            for material in mesh.get_materials():
                if not material:
                    continue
                mat = {"path": material.get_path_name(), "scalars": {}, "vectors": {}}
                try:
                    for name in unreal.MaterialEditingLibrary.get_scalar_parameter_names(material):
                        mat["scalars"][str(name)] = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, name)
                    for name in unreal.MaterialEditingLibrary.get_vector_parameter_names(material):
                        mat["vectors"][str(name)] = str(unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(material, name))
                except Exception as exc:
                    mat["read_error"] = str(exc)
                item["materials"].append(mat)
            record["meshes"].append(item)
        records.append(record)
    Path(r"F:\Carnival\Saved\IndustrialHospital\Sky_Audit.json").write_text(json.dumps(records, indent=2))
    return records

def variant_hook(variant, world, eas):
    if variant["name"] == "02_NoSkyMeshesOrAtmosphere":
        for actor in sky_actors:
            actor.set_is_temporarily_hidden_in_editor(True)
    elif variant["name"] == "03_SkyboxScale1":
        for actor in sky_actors:
            if "LightingNightSnow" in actor.get_level().get_path_name():
                actor.set_is_temporarily_hidden_in_editor(False)
                actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
    elif variant["name"] == "04_SkyboxScale10":
        for actor in sky_actors:
            if "LightingNightSnow" in actor.get_level().get_path_name():
                actor.set_actor_scale3d(unreal.Vector(10, 10, 10))

runpy.run_path(r"F:\Carnival\Scripts\capture_industrial_hospital_connected.py", init_globals={
    "CAPTURE_OUTPUT": "Saved/IndustrialHospital/Previews/SkyScaleDiagnosis",
    "CAPTURE_SETUP": setup,
    "CAPTURE_VARIANT_HOOK": variant_hook,
    "CAPTURE_VARIANTS": [
        {"name": "01_NoAtmosphere", "commands": ["r.BloomQuality 0", "r.SkyAtmosphere 0", "r.VolumetricCloud 0"]},
        {"name": "02_NoSkyMeshesOrAtmosphere", "commands": []},
        {"name": "03_SkyboxScale1", "commands": ["r.SkyAtmosphere 1", "r.BloomQuality 5"]},
        {"name": "04_SkyboxScale10", "commands": []},
    ],
})
