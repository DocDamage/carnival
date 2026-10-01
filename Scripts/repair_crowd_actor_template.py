"""Supply the missing medium-LOD actor using the configured MetaHuman actor class."""
import datetime
import hashlib
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/CrowdAcceptance'
OUT.mkdir(parents=True, exist_ok=True)
REPORT = {'success': False, 'errors': [], 'density_changed': False, 'appearance_changed': False,
          'lod_distances_changed': False, 'maps_modified': False}
try:
    package = '/Game/Carnival/Crowd/Mass/DA_CarnivalCrowdEntityConfig'
    file = ROOT / 'Content/Carnival/Crowd/Mass/DA_CarnivalCrowdEntityConfig.uasset'
    backup = OUT / 'Backups' / datetime.datetime.now(datetime.timezone.utc).strftime('ActorTemplate_%Y%m%d_%H%M%S')
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(file, backup / file.name)
    REPORT['backup'] = str(backup / file.name)
    REPORT['sha256_before'] = hashlib.sha256(file.read_bytes()).hexdigest()
    assert hashlib.sha256((backup / file.name).read_bytes()).hexdigest() == REPORT['sha256_before']
    config = unreal.load_asset(package)
    assert config
    traits = config.get_editor_property('config').get_editor_property('traits')
    visual = next(t for t in traits if t.get_class().get_name() == 'MetaHumanMassCrowdVisualizationTrait')
    high = visual.get_editor_property('high_res_template_actor')
    low = visual.get_editor_property('low_res_template_actor')
    assert high and high.get_path_name() in (
        '/MetaHumanCrowd/BP_CrowdActor.BP_CrowdActor_C',
        '/Game/Carnival/Crowd/Actors/BP_CarnivalCrowdActor.BP_CarnivalCrowdActor_C'), 'Unexpected high-resolution actor'
    assert low is None or low == high, 'Existing different medium-resolution actor requires inspection'
    appearances = [a.get_path_name() for a in visual.get_editor_property('character_instances')]
    params = str(visual.get_editor_property('params'))
    lod_params = str(visual.get_editor_property('lod_params'))
    REPORT['high_actor'] = high.get_path_name()
    REPORT['low_actor_before'] = low.get_path_name() if low else None
    visual.set_editor_property('low_res_template_actor', high)
    assert [a.get_path_name() for a in visual.get_editor_property('character_instances')] == appearances
    assert str(visual.get_editor_property('params')) == params
    assert str(visual.get_editor_property('lod_params')) == lod_params
    assert unreal.EditorAssetLibrary.save_loaded_asset(config, False)
    REPORT.update(success=True, low_actor_after=visual.get_editor_property('low_res_template_actor').get_path_name(),
                  sha256_after=hashlib.sha256(file.read_bytes()).hexdigest(),
                  limits='Configuration repair only; a fresh near-view rendered run must prove actor spawning and transitions.')
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT / 'ActorTemplateRepair_20260930.json').write_text(json.dumps(REPORT, indent=2))
