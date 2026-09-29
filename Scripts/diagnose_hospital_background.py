"""Isolate background geometry and post processing without changing saved maps."""
import json
import runpy
from pathlib import Path
import unreal

candidates = []

def setup(world, eas):
    records = []
    for actor in eas.get_all_level_actors():
        origin, extent = actor.get_actor_bounds(False, True)
        components = actor.get_components_by_class(unreal.StaticMeshComponent)
        post = actor.get_components_by_class(unreal.PostProcessComponent)
        materials = [m.get_path_name() for c in components for m in c.get_materials() if m]
        if not post and max(extent.to_tuple()) < 50000 and not any("sky" in m.lower() for m in materials):
            continue
        record = {"label": actor.get_actor_label(), "class": actor.get_class().get_name(),
                  "level": actor.get_level().get_path_name(), "origin": origin.to_tuple(),
                  "extent": extent.to_tuple(), "materials": sorted(set(materials))}
        record["post_process"] = [str(c.get_editor_property("settings")) for c in post]
        records.append(record)
        if components and (max(extent.to_tuple()) > 500000 or any("sky" in m.lower() for m in materials)):
            candidates.append(actor)
    Path(r"F:\Carnival\Saved\IndustrialHospital\Background_Audit.json").write_text(json.dumps(records, indent=2))
    return {"candidate_labels": [a.get_actor_label() for a in candidates]}

def variant_hook(variant, world, eas):
    if variant["name"] == "03_BackgroundMeshesHidden":
        for actor in candidates:
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                component.set_visibility(False)

runpy.run_path(r"F:\Carnival\Scripts\capture_industrial_hospital_connected.py", init_globals={
    "CAPTURE_OUTPUT": "Saved/IndustrialHospital/Previews/BackgroundDiagnosis",
    "CAPTURE_SETUP": setup, "CAPTURE_VARIANT_HOOK": variant_hook,
    "CAPTURE_VARIANTS": [
        {"name": "01_NoPostProcess", "commands": ["showflag.PostProcessing 0"]},
        {"name": "02_NoAtmosphereFogOrTranslucency", "commands": ["r.SkyAtmosphere 0", "r.Fog 0", "r.LocalFogVolume 0", "showflag.Translucency 0"]},
        {"name": "03_BackgroundMeshesHidden", "commands": []},
    ],
})
