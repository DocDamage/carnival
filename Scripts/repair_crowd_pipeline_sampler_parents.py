"""Persist the completed local skin repair in existing crowd build overrides.

Use native UPROPERTY names: an editor pipeline wrapped as its Python base class
does not have snake_case mappings for subclass-only reflected properties.
"""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT/'Saved/CharacterRepairs'
BACKUP = OUT/('CrowdPipelineBackup_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
REPORT = {'collections': [], 'backups': [], 'saved_packages': [], 'errors': [], 'status': 'not_started'}


def object_path(value):
    if not value:
        return None
    return value.get_path_name() if hasattr(value, 'get_path_name') else str(value)


try:
    previous = json.loads((OUT/'CrowdSamplerRepair.json').read_text())
    assert previous['status'].startswith('saved'), 'Local material repair must already be saved'
    mapping = {item['source']: item['local'] for item in previous['cloned_assets']}
    inventory = json.loads((OUT/'CrowdSamplerGraph.json').read_text())
    for key in inventory['collections']:
        package = key.split('.')[0]
        assert package.startswith('/Game/Carnival/Crowd/Collections/')
        collection = unreal.load_asset(package)
        pipeline = collection.get_editor_property('Pipeline')
        editor = pipeline.get_editor_property('EditorPipeline')
        overrides = editor.get_editor_property('FaceMaterialOverrides')
        row = {'collection': key, 'override_count': len(overrides), 'changes': []}
        REPORT['collections'].append(row)
        for extension in ('.uasset', '.uexp', '.ubulk'):
            relative = package[len('/Game/'):] + extension
            source = ROOT/'Content'/relative
            if source.exists():
                destination = BACKUP/relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                REPORT['backups'].append({'file': str(destination), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})
        for override in overrides:
            slot = str(override.get_editor_property('SlotName'))
            for field in ('ActorMaterial', 'InstancedMaterial'):
                old = object_path(override.get_editor_property(field))
                if old in mapping:
                    replacement = unreal.load_asset(mapping[old])
                    assert replacement, mapping[old]
                    override.set_editor_property(field, replacement)
                    row['changes'].append({'slot': slot, 'field': field, 'old': old, 'new': replacement.get_path_name()})
                elif old and 'skin_unified_baked_crowd' in old and not old.startswith('/Game/Carnival/Crowd/Materials/SamplerRepair/'):
                    REPORT['errors'].append('Unmapped skin parent '+old+' in '+key+' '+field)
        if row['changes']:
            editor.set_editor_property('FaceMaterialOverrides', overrides)
            assert unreal.EditorAssetLibrary.save_loaded_asset(collection, only_if_is_dirty=False), package
            REPORT['saved_packages'].append(package)
        if not overrides:
            REPORT['errors'].append('No existing override mappings in '+key)
    REPORT['status'] = 'saved' if not REPORT['errors'] else 'incomplete'
except Exception:
    REPORT['status'] = 'failed'
    REPORT['errors'].append(traceback.format_exc())
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'CrowdPipelineRepair.json').write_text(json.dumps(REPORT, indent=2))
    unreal.log('CROWD_PIPELINE_REPAIR '+json.dumps(REPORT))
    unreal.SystemLibrary.quit_editor()
