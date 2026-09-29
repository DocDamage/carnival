"""Audit the runtime controller defaults and mapped keys for player recovery."""

import json
from pathlib import Path

import unreal


OUT = Path(r"F:\Carnival\Saved\HauntedDollIntegration\Recovery_Input_Mapping.json")
CONTROLLER_BP = "/Game/Carnival/Blueprints/BP_CarnivalPlayerController"
PLAYER_CONTEXT = "/Game/Carnival/Input/IMC_CarnivalPlayer"


report = {"controller_blueprint": CONTROLLER_BP, "mapping_context": PLAYER_CONTEXT}
blueprint = unreal.load_asset(CONTROLLER_BP)
if not blueprint:
    raise RuntimeError(f"Could not load {CONTROLLER_BP}")
generated_class = blueprint.generated_class()
if not generated_class:
    raise RuntimeError("Player controller Blueprint has no generated class")
defaults = unreal.get_default_object(generated_class)
report["default_object"] = {
    "name": defaults.get_name(),
    "class": defaults.get_class().get_path_name(),
}
report["controller_defaults"] = {}
for property_name in ("cancel_action", "play_station_prompts", "default_mapping_context"):
    try:
        value = defaults.get_editor_property(property_name)
        report["controller_defaults"][property_name] = (
            value.get_path_name() if hasattr(value, "get_path_name") else value
        )
    except Exception as error:
        report["controller_defaults"][property_name] = f"error: {error}"

context = unreal.load_asset(PLAYER_CONTEXT)
if not context:
    raise RuntimeError(f"Could not load {PLAYER_CONTEXT}")
report["context_mapping_api"] = [name for name in dir(context) if "mapping" in name.lower()]
mapping_data = context.get_editor_property("default_key_mappings")
report["mapping_data_type"] = str(type(mapping_data))
report["mapping_data_members"] = [name for name in dir(mapping_data) if not name.startswith("_")]
report["mapping_data_fields"] = {}
mappings = []
for field_name in ("mappings", "default_mappings", "key_mappings", "default_key_mappings"):
    try:
        value = mapping_data.get_editor_property(field_name)
        if hasattr(value, "__iter__"):
            value = list(value)
        report["mapping_data_fields"][field_name] = {
            "type": str(type(value)),
            "length": len(value) if hasattr(value, "__len__") else None,
        }
        if isinstance(value, list) and value:
            mappings = value
            report["mapping_property"] = field_name
            break
    except Exception as error:
        report["mapping_data_fields"][field_name] = {"error": str(error)}
report["mappings"] = []
for mapping in mappings:
    try:
        action = mapping.get_editor_property("action")
        key = mapping.get_editor_property("key")
        row = {"action": action.get_path_name() if action else None,
               "key_text": str(key) if key else None,
               "key_tuple": list(key.to_tuple()) if key else None,
               "key_dict": key.to_dict() if key else None}
        row["key_fields"] = {}
        if key:
            for field_name in ("key_name", "name", "key_name_string"):
                try:
                    row["key_fields"][field_name] = str(key.get_editor_property(field_name))
                except Exception:
                    pass
        modifiers = mapping.get_editor_property("modifiers")
        row["modifiers"] = [modifier.get_class().get_name() for modifier in modifiers]
        report["mappings"].append(row)
    except Exception as error:
        report["mappings"].append({"error": str(error), "members": [name for name in dir(mapping) if not name.startswith("_")]})

cancel_action = report["controller_defaults"].get("cancel_action")
report["recovery_bindings"] = [row for row in report["mappings"]
                               if row.get("action") == cancel_action]
report["backspace_is_mapped"] = any("BackSpace" in json.dumps(row) for row in report["recovery_bindings"])
report["playstation_circle_is_mapped"] = any("FaceButton_Right" in json.dumps(row)
                                             for row in report["recovery_bindings"])
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("RECOVERY_INPUT_MAPPING " + json.dumps({
    "cancel_action": cancel_action,
    "recovery_bindings": report["recovery_bindings"],
    "backspace_is_mapped": report["backspace_is_mapped"],
    "playstation_circle_is_mapped": report["playstation_circle_is_mapped"],
    "report": str(OUT),
}))
unreal.SystemLibrary.quit_editor()
