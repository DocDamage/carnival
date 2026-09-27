import json
from pathlib import Path
import unreal

result = {}
for name in (
    "SoundWave", "SoundCue", "SoundCueFactoryNew", "SoundNodeLooping",
    "SoundNodeWavePlayer", "SoundAttenuation", "SoundAttenuationFactory",
    "SoundAttenuationSettings", "AudioComponent", "AmbientSound",
):
    cls = getattr(unreal, name, None)
    if cls is None:
        result[name] = None
        continue
    try:
        default = cls()
    except Exception:
        default = None
    doc = getattr(cls, "__doc__", "") or ""
    relevant = {}
    for key in (
        "looping", "duration", "num_channels", "sample_rate", "attenuation_settings",
        "override_attenuation", "attenuation_overrides", "attenuation_shape",
        "attenuation_shape_extents", "falloff_distance", "attenuation_function",
        "spatialization_method", "volume_attenuation_distance_model",
    ):
        if default:
            try:
                relevant[key] = repr(default.get_editor_property(key))
            except Exception:
                pass
    result[name] = {
        "doc": doc[:6000],
        "factory": getattr(cls, "__doc__", None),
        "members": {member: getattr(getattr(cls, member, None), "__doc__", None)
                    for member in dir(cls)
                    if any(term in member.lower() for term in
                           ("loop", "sound", "attenuation", "child", "node", "input", "volume"))},
        "default_properties": relevant,
    }

Path(r"F:\Carnival\Saved\IndustrialHospital\Audio_Authoring_API.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)
unreal.log("INDUSTRIAL_HOSPITAL_AUDIO_AUTHORING_API_SAVED")
