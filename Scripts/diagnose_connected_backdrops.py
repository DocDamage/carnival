"""Check the coastal source pack's large photographic backdrop planes."""
import json
import runpy
from pathlib import Path
import unreal

backdrops = []
groups = {"cloud": [], "coast_fog": [], "hospital_vfx": [], "emitters": []}

def setup(world, eas):
    records = []
    for actor in eas.get_all_level_actors():
        if actor.get_class().get_name() == "BP_Fake_Cloud_C":
            groups["cloud"].append(actor)
        if "LV_Hospital_VFX" in actor.get_level().get_path_name():
            groups["hospital_vfx"].append(actor)
        if actor.get_components_by_class(unreal.ParticleSystemComponent) or actor.get_components_by_class(unreal.NiagaraComponent):
            groups["emitters"].append(actor)
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            for material in component.get_materials():
                if material and "/RailBridge/Materials/MI_ParticleFog" in material.get_path_name():
                    groups["coast_fog"].append(actor)
                if not material or "/RailBridge/Materials/MI_BG_" not in material.get_path_name():
                    continue
                backdrops.append(component)
                records.append({"label": actor.get_actor_label(), "material": material.get_path_name(),
                    "scalars": {str(n): unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, n)
                                for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(material)},
                    "vectors": {str(n): str(unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(material, n))
                                for n in unreal.MaterialEditingLibrary.get_vector_parameter_names(material)}})
    Path(r"F:\Carnival\Saved\IndustrialHospital\Backdrop_Audit.json").write_text(json.dumps(records, indent=2))
    return {"backdrops": records, "groups": {name: [a.get_actor_label() for a in actors] for name, actors in groups.items()}}

def variant_hook(variant, world, eas):
    for component in backdrops:
        component.set_visibility(False)
    group = variant.get("group")
    if group:
        for actor in groups[group]:
            for component in actor.get_components_by_class(unreal.SceneComponent):
                component.set_visibility(False, True)

runpy.run_path(r"F:\Carnival\Scripts\capture_industrial_hospital_connected.py", init_globals={
    "CAPTURE_OUTPUT": "Saved/IndustrialHospital/Previews/BackdropDiagnosis",
    "CAPTURE_SETUP": setup, "CAPTURE_VARIANT_HOOK": variant_hook,
    "CAPTURE_VARIANTS": [
        {"name": "01_CoastalBackdropsHidden", "commands": []},
        {"name": "02_AlsoFakeCloudsHidden", "commands": [], "group": "cloud"},
        {"name": "03_AlsoCoastalFogHidden", "commands": [], "group": "coast_fog"},
        {"name": "04_AlsoHospitalVFXHidden", "commands": [], "group": "hospital_vfx"},
        {"name": "05_AlsoEmittersHidden", "commands": [], "group": "emitters"},
    ],
})
