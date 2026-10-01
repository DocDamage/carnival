"""Fresh-process readback of resaved legacy material layers; never save."""
import json, re, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT/'Saved/PresentationAcceptance/LegacyMaterialStateRepair_20260930'
previous = json.loads((OUT/'index.json').read_text())
REPORT = {'success': False, 'errors': [], 'assets': [], 'assets_modified': False}
try:
    assert previous['success']
    for row in previous['assets']:
        asset = unreal.load_asset(row['package']); assert asset
        actual = unreal.CarnivalCrowdEditorLibrary.get_material_function_state_id(asset)
        assert len(actual) == 32 and int(actual,16) != 0, 'Invalid zero state GUID'
        assert actual == row['state_id_after'], 'State GUID changed across fresh reload'
        for name, value in row['parameters'].items():
            assert re.sub(r'0x[0-9a-fA-F]+', '<address>', str(asset.get_editor_property(name))) == value
        REPORT['assets'].append({'package': row['package'], 'state_id': actual})
    REPORT['success'] = True
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT/'Reload.json').write_text(json.dumps(REPORT, indent=2))
