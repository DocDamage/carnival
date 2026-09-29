"""Compare rendering causes at one hospital viewpoint without saving assets."""
import runpy

runpy.run_path(r"F:\Carnival\Scripts\capture_industrial_hospital_connected.py", init_globals={
    "CAPTURE_OUTPUT": "Saved/IndustrialHospital/Previews/GlareDiagnosis",
    "CAPTURE_VARIANTS": [
        {"name": "01_Baseline", "commands": ["r.BloomQuality 5", "r.Fog 1", "r.LocalFogVolume 1", "r.EyeAdaptationQuality 2"]},
        {"name": "02_NoBloom", "commands": ["r.BloomQuality 0"]},
        {"name": "03_NoBloomOrFog", "commands": ["r.Fog 0", "r.LocalFogVolume 0"]},
        {"name": "04_NoBloomFogOrAdaptation", "commands": ["r.EyeAdaptationQuality 0"]},
    ],
})
