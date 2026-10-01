"""Back up the main map and replace only its owned guest spawn generator."""
import datetime, hashlib, json, math, shutil, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT/'Saved/CrowdAcceptance/DistinctSpawnRepair_20260930'
OUT.mkdir(parents=True, exist_ok=True)
BACKUP = OUT/'Backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
BACKUP.mkdir(parents=True, exist_ok=False)
MAP = '/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
SOURCE = ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
REPORT = {'success': False, 'errors': [], 'map': MAP, 'count_changed': False,
          'routes_changed': False, 'appearance_changed': False}

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def snapshot(spawner):
    return {'count': spawner.get_count(), 'scale': spawner.get_spawning_count_scale(),
            'auto_spawn': spawner.get_editor_property('auto_spawn_on_begin_play'),
            'location': list(spawner.get_actor_location().to_tuple()),
            'types': [{'config': t.get_editor_property('entity_config').get_path_name(),
                       'proportion': t.get_editor_property('proportion')}
                      for t in spawner.get_editor_property('entity_types')]}
def preview(world):
    points, error = unreal.CarnivalCrowdEditorLibrary.preview_crowd_spawn_locations(world)
    assert not error, error
    points = [list(p.to_tuple()) for p in points]
    distances = [math.dist(a[:2], b[:2]) for i,a in enumerate(points) for b in points[i+1:]]
    return {'positions': points, 'count': len(points), 'unique_positions': len(set(tuple(p) for p in points)),
            'minimum_distance_cm': min(distances), 'coincident_pairs': sum(d < .01 for d in distances),
            'pairs_below_80cm': sum(d < 80 for d in distances)}

try:
    target = BACKUP/SOURCE.name
    shutil.copy2(SOURCE, target)
    REPORT.update(backup=str(target), sha256_before=digest(SOURCE))
    assert digest(target) == REPORT['sha256_before']
    assert unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    spawners = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MassSpawner)
    assert len(spawners) == 1
    spawner = spawners[0]
    before = snapshot(spawner)
    assert before['count'] == 240 and before['scale'] == 1 and before['auto_spawn']
    REPORT['spawner_before'] = before
    REPORT['lanes_before'] = list(unreal.CarnivalCrowdEditorLibrary.describe_crowd_lanes(world))
    REPORT['before'] = preview(world)
    # Unreal exposes bool success plus an out parameter as that output on success,
    # or None on failure, rather than as a (bool, output) tuple.
    error = unreal.CarnivalCrowdEditorLibrary.configure_distinct_crowd_spawn_positions(spawner)
    assert error == '', error
    # Repeating the configuration must retain the same generator instance.
    generator = spawner.get_editor_property('spawn_data_generators')[0].get_editor_property('generator_instance')
    error = unreal.CarnivalCrowdEditorLibrary.configure_distinct_crowd_spawn_positions(spawner)
    assert error == '', error
    assert generator == spawner.get_editor_property('spawn_data_generators')[0].get_editor_property('generator_instance')
    REPORT['generator'] = generator.get_class().get_name()
    REPORT['spacing_cm'] = generator.get_editor_property('spacing')
    REPORT['radius_cm'] = generator.get_editor_property('agent_radius')
    REPORT['after'] = preview(world)
    assert REPORT['after']['count'] == REPORT['after']['unique_positions'] == 240
    assert REPORT['after']['minimum_distance_cm'] >= 99.99
    assert snapshot(spawner) == before
    REPORT['lanes_after'] = list(unreal.CarnivalCrowdEditorLibrary.describe_crowd_lanes(world))
    assert REPORT['lanes_after'] == REPORT['lanes_before']
    assert unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
    REPORT.update(success=True, sha256_after=digest(SOURCE))
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT, indent=2))
