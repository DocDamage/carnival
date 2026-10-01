"""Add native lane roaming to the owned crowd config; preserve appearance and density."""
import datetime
import hashlib
import json
import os
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT/'Saved/CrowdAcceptance'
BACKUP = OUT/'Backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
BACKUP.mkdir(parents=True, exist_ok=False)
CONFIG = '/Game/Carnival/Crowd/Mass/DA_CarnivalCrowdEntityConfig'
BEHAVIOR = '/Game/Carnival/Crowd/Behavior/ST_CarnivalGuestRoaming'
REPORT = {'success': False, 'assets': [], 'errors': [], 'spawner_count_changed': False,
          'maps_modified': False, 'appearance_changed': False}

def backup(package):
    source = ROOT/'Content'/Path(package.removeprefix('/Game/')).with_suffix('.uasset')
    if source.exists():
        target = BACKUP/source.name
        shutil.copy2(source, target)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
        REPORT['assets'].append({'package': package, 'backup': str(target), 'sha256_before': digest})
    else:
        REPORT['assets'].append({'package': package, 'new_asset': True})

try:
    backup(CONFIG); backup(BEHAVIOR)
    config = unreal.load_asset(CONFIG)
    assert config
    before = list(config.get_editor_property('config').get_editor_property('traits'))
    visualization = next(t for t in before if t.get_class().get_name() == 'MetaHumanMassCrowdVisualizationTrait')
    instances = [a.get_path_name() for a in visualization.get_editor_property('character_instances')]
    tree, error = unreal.CarnivalCrowdEditorLibrary.configure_crowd_roaming(config, BEHAVIOR)
    if not tree or error: raise RuntimeError(error or 'No compiled roaming behavior')
    after = list(config.get_editor_property('config').get_editor_property('traits'))
    required = {'CarnivalCrowdNavigationPrerequisiteTrait', 'MassMovementTrait', 'MassSteeringTrait',
                'MassZoneGraphNavigationTrait', 'MassObstacleAvoidanceTrait', 'MassNavigationObstacleTrait',
                'MassSmoothOrientationTrait', 'MassStateTreeTrait'}
    classes = [t.get_class().get_name() for t in after]
    assert required <= set(classes)
    assert len(classes) == len(set(classes)), 'Duplicate crowd traits'
    assert [a.get_path_name() for a in visualization.get_editor_property('character_instances')] == instances
    behavior_trait = next(t for t in after if t.get_class().get_name() == 'MassStateTreeTrait')
    assert behavior_trait.get_editor_property('state_tree') == tree
    assert unreal.EditorAssetLibrary.save_loaded_asset(tree, False)
    assert unreal.EditorAssetLibrary.save_loaded_asset(config, False)
    REPORT.update(success=True, traits_before=[t.get_class().get_name() for t in before], traits_after=classes,
                  character_instances=instances, behavior=tree.get_path_name())
    avoidance = next(t for t in after if t.get_class().get_name() == 'MassObstacleAvoidanceTrait')
    moving = avoidance.get_editor_property('moving_parameters')
    standing = avoidance.get_editor_property('standing_parameters')
    REPORT['moving_avoidance'] = {name: moving.get_editor_property(name) for name in (
        'start_of_path_avoidance_scale', 'end_of_path_avoidance_scale', 'standing_obstacle_avoidance_scale',
        'separation_radius_scale', 'predictive_avoidance_radius_scale', 'obstacle_separation_stiffness')}
    REPORT['standing_avoidance'] = {name: standing.get_editor_property(name) for name in (
        'ghost_separation_radius_scale', 'ghost_separation_distance')}
    assert all(value == 1 for name, value in REPORT['moving_avoidance'].items() if name.endswith('scale'))
    for row in REPORT['assets']:
        source = ROOT/'Content'/Path(row['package'].removeprefix('/Game/')).with_suffix('.uasset')
        row['sha256_after'] = hashlib.sha256(source.read_bytes()).hexdigest()
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT/os.environ.get('CARNIVAL_CROWD_AUTHOR_REPORT', 'RoamingAuthoring_20260930.json')).write_text(json.dumps(REPORT, indent=2))
