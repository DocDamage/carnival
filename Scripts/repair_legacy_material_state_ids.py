"""Back up and resave four measured legacy material layers, without changing parameters."""
import datetime, hashlib, json, re, shutil, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT/'Saved/PresentationAcceptance/LegacyMaterialStateRepair_20260930'
OUT.mkdir(parents=True, exist_ok=True)
BACKUP = OUT/'Backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
BACKUP.mkdir(parents=True, exist_ok=False)
REPORT = {'success': False, 'errors': [], 'assets': [], 'maps_modified': False,
          'limits': 'Resave the four assets named by actual invalid-StateId load warnings. Fresh reload must verify stable state IDs and absence of those warnings; no frame-rate acceptance.'}
NAMES = ('ML_Buoy_Paint_01a', 'ML_Buoy_Rust_01a', 'ML_Ballast', 'ML_RR_Grade_Unique')

def parameters(asset):
    # Strip wrapper addresses; keep the reflected names, values and asset paths.
    return {name: re.sub(r'0x[0-9a-fA-F]+', '<address>', str(asset.get_editor_property(name))) for name in (
        'parent', 'scalar_parameter_values', 'vector_parameter_values', 'double_vector_parameter_values',
        'texture_parameter_values', 'texture_collection_parameter_values', 'parameter_collection_parameter_values',
        'font_parameter_values', 'static_switch_parameter_values', 'static_component_mask_parameter_values',
        'runtime_virtual_texture_parameter_values', 'sparse_volume_texture_parameter_values')}

def state_id(asset):
    return unreal.CarnivalCrowdEditorLibrary.get_material_function_state_id(asset)

try:
    for name in NAMES:
        package = '/Game/RailBridge/Materials/LayeredMaterial/'+name
        file = ROOT/'Content'/Path(package.removeprefix('/Game/')).with_suffix('.uasset')
        target = BACKUP/file.name; shutil.copy2(file, target)
        row = {'package': package, 'backup': str(target), 'sha256_before': hashlib.sha256(file.read_bytes()).hexdigest()}
        REPORT['assets'].append(row)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == row['sha256_before']
        asset = unreal.load_asset(package); assert asset
        assert isinstance(asset, unreal.MaterialFunctionMaterialLayerInstance)
        before = parameters(asset)
        row['class'] = asset.get_class().get_name()
        row['state_id_loaded'] = state_id(asset)
        assert len(row['state_id_loaded']) == 32 and int(row['state_id_loaded'], 16) != 0, 'Loaded layer has no valid state GUID'
        assert unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
        assert parameters(asset) == before
        row.update(parameters=before, state_id_after=state_id(asset),
                   sha256_after=hashlib.sha256(file.read_bytes()).hexdigest())
        assert row['state_id_after'] == row['state_id_loaded']
    REPORT['success'] = True
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT, indent=2))
