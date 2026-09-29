"""Thirty-second process-only GameInput enumeration; never saves configuration."""
import json
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)

OUT=Path(unreal.Paths.project_dir())/'Saved/InputDiagnostics'
OUT.mkdir(parents=True,exist_ok=True)
S={'start':time.monotonic(),'samples':[]}

def tick(_):
    elapsed=time.monotonic()-S['start']
    if elapsed<len(S['samples'])*5: return
    settings=unreal.find_object(None,'/Engine/Transient.GameInputPlatformSettings_Windows')
    row={'elapsed_seconds':elapsed,'settings_found':bool(settings)}
    if settings:
        for field in ('process_gamepad','process_controller','process_raw_input','special_devices_require_explicit_device_configuration'):
            try: row[field]=settings.get_editor_property(field)
            except Exception as exc: row[field]=str(exc)
    S['samples'].append(row)
    (OUT/'GameInput_Process_Settings.json').write_text(json.dumps(S['samples'],indent=2))
    unreal.log('GAMEINPUT_PROCESS_INSPECTION '+json.dumps(row))
    if elapsed>=30:
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.SystemLibrary.quit_editor()

handle=unreal.register_slate_post_tick_callback(tick)
