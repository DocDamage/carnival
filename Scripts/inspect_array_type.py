import json
from pathlib import Path
import unreal

info = {
    "repr": repr(unreal.Array),
    "type": str(type(unreal.Array)),
    "doc": unreal.Array.__doc__,
    "dir": [n for n in dir(unreal.Array) if not n.startswith("_")],
    "cast_doc": unreal.Array.cast.__doc__,
    "actor_array": repr(unreal.Array(unreal.Actor)),
    "actor_array_type": str(type(unreal.Array(unreal.Actor))),
}
Path(r"F:\Carnival\Saved\IndustrialHospital\Array_Type.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
unreal.log("INDUSTRIAL_ARRAY_TYPE_SAVED")
unreal.SystemLibrary.quit_editor()
