"""Back up and guard the inspected imported ride parent's empty announcement queue."""
import datetime
import hashlib
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/RideDevelopment/AnnouncementQueue'
OUT.mkdir(parents=True, exist_ok=True)
REPORT = {'success': False, 'errors': [], 'audio_disabled': False}
try:
    package = '/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/Structure/BP_Rides_Parent'
    file = ROOT / 'Content' / Path(package.removeprefix('/Game/')).with_suffix('.uasset')
    backup = OUT / 'Backups' / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(file, backup / file.name)
    REPORT['backup'] = str(backup / file.name)
    REPORT['sha256_before'] = hashlib.sha256(file.read_bytes()).hexdigest()
    assert hashlib.sha256((backup / file.name).read_bytes()).hexdigest() == REPORT['sha256_before']
    bp = unreal.load_asset(package)
    assert bp
    REPORT['before_graph'] = list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(bp))
    result = unreal.CarnivalBalloonFlightComponent.repair_empty_announcement_queue(bp)
    assert result in (0, 1), 'Announcement graph no longer matches inspected execution'
    REPORT['changed'] = result == 1
    assert unreal.CarnivalBalloonFlightComponent.repair_empty_announcement_queue(bp) == 0, 'Repair is not idempotent'
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert bp.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR, 'Parent Blueprint compilation failed'
    REPORT['after_graph'] = list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(bp))
    assert any('Carnival_AnnouncementQueueReady' in line for line in REPORT['after_graph'])
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    REPORT.update(success=True, sha256_after=hashlib.sha256(file.read_bytes()).hexdigest(),
                  limits='Requires fresh runtime empty, populated, exhausted and refill queue checks. Audio audition remains separate.')
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT / 'Repair_20260930.json').write_text(json.dumps(REPORT, indent=2))
