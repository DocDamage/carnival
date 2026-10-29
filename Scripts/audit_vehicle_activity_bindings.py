"""Audit (or fill missing) owned vehicle context/cancel mappings with backup hashes."""
import hashlib
import json
import os
import shutil
import traceback
from pathlib import Path

import unreal

ROOT = Path(r'F:\Carnival')
APPLY = os.environ.get('CARNIVAL_FIX_VEHICLE_BINDINGS') == '1'
OUT = ROOT / ('Saved/InputCleanup/VehicleActivityBindings_20261029' + ('_Applied' if APPLY else '_Audit'))
OUT.mkdir(parents=True, exist_ok=False)
R = {'success': False, 'errors': [], 'contexts': {}, 'missing': [], 'conflicts': [], 'modified': False}


def rows(context):
    return [(m.get_editor_property('action'), str(m.get_editor_property('key').get_editor_property('key_name')))
            for m in context.get_editor_property('default_key_mappings').get_editor_property('mappings')]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


try:
    bp = unreal.load_asset('/Game/Carnival/Blueprints/BP_CarnivalPlayerController')
    cdo = unreal.get_default_object(bp.generated_class())
    contexts = [cdo.get_editor_property(p) for p in ('default_mapping_context', 'motorcycle_mapping_context')]
    for context in contexts:
        R['contexts'][context.get_path_name()] = [{'action': a.get_path_name() if a else None, 'key': k} for a, k in rows(context)]
    required = [(cdo.get_editor_property('context_interact_action'), k) for k in ('E', 'Gamepad_DPad_Right')]
    required += [(cdo.get_editor_property('cancel_action'), k) for k in ('BackSpace', 'Gamepad_FaceButton_Right')]
    target = contexts[1]
    existing = rows(target)
    missing = [(a, k) for a, k in required if (a, k) not in existing]
    R['missing'] = [{'action': a.get_path_name(), 'key': k} for a, k in missing]
    R['conflicts'] = [{'key': k, 'required': a.get_path_name(), 'existing': other.get_path_name()}
                      for a, k in missing for other, key in existing if key == k and other != a and other]
    if APPLY and missing:
        assert not R['conflicts'], R['conflicts']
        package = target.get_path_name().split('.')[0]
        assert package.startswith('/Game/Carnival/Input/')
        file = ROOT / ('Content/' + package.removeprefix('/Game/') + '.uasset')
        backup = Path(r'D:\CarnivalBackups\vehicle_activity_bindings_20261029')
        backup.mkdir(parents=True, exist_ok=False)
        R['before_sha256'] = sha(file)
        for destination in (OUT / (file.stem + '.before.uasset'), backup / (file.stem + '.before.uasset')):
            shutil.copy2(file, destination)
            assert sha(destination) == R['before_sha256']
        target.modify()
        for action, name in missing:
            key = unreal.Key()
            key.set_editor_property('key_name', unreal.Name(name))
            target.map_key(action, key)
        assert all(pair in rows(target) for pair in required)
        assert unreal.EditorAssetLibrary.save_loaded_asset(target, False)
        R['after_sha256'] = sha(file)
        shutil.copy2(file, backup / file.name)
        assert sha(backup / file.name) == R['after_sha256']
        R.update(modified=True, external_backup=str(backup))
    R['complete'] = all(pair in rows(target) for pair in required)
    R['success'] = True
except Exception:
    R['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT / 'index.json').write_text(json.dumps(R, indent=2))
