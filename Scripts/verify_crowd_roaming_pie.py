"""Measure real Mass guest movement in the full map; never move entities or player.

NullRHI establishes simulation only. Optional render-pie captures require visual
review; neither mode accepts packaged frame rate.
"""
import json
import math
import os
import struct
import sys
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'Scripts'))
from crowd_lighting_survey import survey
OUT = ROOT / 'Saved/CrowdAcceptance' / os.environ.get('CARNIVAL_CROWD_REPORT', 'RoamingPIE_20260930')
OUT.mkdir(parents=True, exist_ok=True)
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT = {'success': False, 'errors': [], 'samples': [], 'entities': [],
          'assets_modified': False, 'player_or_entities_teleported': False,
          'observer': os.environ.get('CARNIVAL_CROWD_OBSERVER', 'arrival'),
          'require_spacing_proxy': os.environ.get('CARNIVAL_CROWD_REQUIRE_SPACING') == '1',
          'performance_acceptance': False, 'visual_acceptance': False,
          'capture_enabled': os.environ.get('CARNIVAL_CROWD_CAPTURE') == '1',
          'captures': [], 'visual_review': 'pending',
          'limits': 'Actual full-map simulation with saved authored spawner and unchanged density. Optional DX12 captures require separate visual review. No packaged performance, controller, queueing or world obstruction acceptance.'}
S = {'phase': 'setup', 'busy': False, 'deadline': time.monotonic() + 1200}


def save():
    REPORT['phase'] = S['phase']
    (OUT / 'index.json').write_text(json.dumps(REPORT, indent=2))


def finish(error=None):
    if error:
        REPORT['errors'].append(error)
    REPORT['success'] = not REPORT['errors'] and bool(REPORT['entities'])
    save()
    LE.editor_request_end_play()
    S.update(phase='exit', deadline=time.monotonic() + 4)


def sample(game):
    rows = []
    for entity in unreal.CarnivalCrowdEditorLibrary.sample_live_crowd_entities(game):
        rows.append({'id': [entity.entity_index, entity.entity_serial],
                     'location': list(entity.location.to_tuple()),
                     'velocity': list(entity.velocity.to_tuple()),
                     'lane': entity.lane_index, 'lane_distance': entity.lane_distance,
                     'behavior_active': entity.behavior_active,
                     'agent_radius': entity.agent_radius, 'in_avoidance_grid': entity.get_editor_property('bInAvoidanceGrid'),
                     'movement_action': entity.movement_action,
                     'steering_falling_behind': entity.steering_falling_behind})
    REPORT['samples'].append({'game_seconds': unreal.GameplayStatics.get_time_seconds(game),
                              'wall_seconds': time.monotonic() - S['started'],
                              'entities': rows})
    save()


def request_capture(game, name):
    if not REPORT['capture_enabled']:
        return
    path = OUT/(name+'.png')
    requested = time.time()
    unreal.SystemLibrary.execute_console_command(game, f'HighResShot 1280x800 filename="{path.as_posix()}"')
    REPORT['captures'].append({'name': name, 'path': str(path), 'requested': requested,
                               'game_seconds': unreal.GameplayStatics.get_time_seconds(game)})
    save()


def evaluate():
    samples = REPORT['samples']
    expected = REPORT['expected_count']
    initial = {tuple(row['id']) for row in samples[0]['entities']}
    if len(initial) != expected:
        REPORT['errors'].append(f'Expected {expected} distinct entities, found {len(initial)}')
    tracked = {key: {'id': list(key), 'path_cm': 0., 'lane_changes': 0, 'max_step_cm': 0.,
                     'missing_samples': 0, 'inactive_samples': 0, 'invalid_lane_samples': 0,
                     'implausible_steps': 0} for key in initial}
    previous = {}
    for capture in samples:
        seen = set()
        for row in capture['entities']:
            key = tuple(row['id'])
            seen.add(key)
            if key not in tracked:
                REPORT['errors'].append('Entity identity changed during measurement')
                continue
            stats = tracked[key]
            stats['inactive_samples'] += int(not row['behavior_active'])
            stats['invalid_lane_samples'] += int(row['lane'] < 0)
            if not all(math.isfinite(v) for v in row['location'] + row['velocity']):
                REPORT['errors'].append('Nonfinite entity transform/velocity')
            if key in previous:
                old, old_time = previous[key]
                distance = math.dist(row['location'], old['location'])
                elapsed = capture['game_seconds'] - old_time
                stats['path_cm'] += distance
                stats['max_step_cm'] = max(stats['max_step_cm'], distance)
                stats['lane_changes'] += int(row['lane'] != old['lane'])
                stats['implausible_steps'] += int(distance > 200 * elapsed + 100)
            previous[key] = row, capture['game_seconds']
        for key in initial - seen:
            tracked[key]['missing_samples'] += 1
    REPORT['entities'] = [tracked[key] for key in sorted(tracked)]
    REPORT['measurement_game_seconds'] = samples[-1]['game_seconds'] - samples[0]['game_seconds']
    for field in ('missing_samples', 'inactive_samples', 'invalid_lane_samples', 'implausible_steps'):
        count = sum(bool(row[field]) for row in REPORT['entities'])
        if count:
            REPORT['errors'].append(f'{count} entities failed {field}')
    stalled = sum(row['path_cm'] < 200 for row in REPORT['entities'])
    if stalled:
        REPORT['errors'].append(f'{stalled} entities moved less than 200cm in 40 game seconds')
    REPORT['moving_entities'] = sum(row['path_cm'] >= 200 for row in REPORT['entities'])
    REPORT['entities_changing_lanes'] = sum(row['lane_changes'] > 0 for row in REPORT['entities'])
    if not REPORT['entities_changing_lanes']:
        REPORT['errors'].append('No actual lane transitions observed')
    REPORT['spacing_diagnostics'] = []
    for capture in samples:
        positions = [row['location'][:2] for row in capture['entities']]
        distances = [math.dist(a, b) for i, a in enumerate(positions) for b in positions[i + 1:]]
        REPORT['spacing_diagnostics'].append({'game_seconds': capture['game_seconds'],
                                              'pairs_closer_than_80cm': sum(d < 80 for d in distances),
                                              'coincident_pairs': sum(d < .01 for d in distances),
                                              'min_separation_cm': min(distances, default=None)})
    REPORT['spacing_proxy_pass'] = all(row['pairs_closer_than_80cm'] == 0 for row in REPORT['spacing_diagnostics'])
    REPORT['spacing_proxy_limits'] = 'Per-second 2D root separation proxy for two 40cm agents; not body contacts, continuous collision or world obstruction acceptance.'
    if any(row['agent_radius'] <= 0 or not math.isfinite(row['agent_radius'])
           for capture in samples for row in capture['entities']):
        REPORT['errors'].append('Guest navigation radius is invalid')
    if REPORT['require_spacing_proxy'] and not REPORT['spacing_proxy_pass']:
        REPORT['errors'].append('Guest root separation remains below the 80cm spacing proxy')


def tick(_):
    if S['busy']:
        return
    S['busy'] = True
    try:
        now = time.monotonic()
        if S['phase'] == 'exit':
            if now > S['deadline']:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        game = unreal.EditorLevelLibrary.get_game_world()
        if now > S['deadline']:
            if game:
                REPORT['timeout_diagnostics'] = list(unreal.CarnivalCrowdEditorLibrary.describe_live_mass_simulation(game))
            finish('Timeout in ' + S['phase'])
            return
        if not game:
            return
        game_time = unreal.GameplayStatics.get_time_seconds(game)
        if S['phase'] == 'setup':
            if not unreal.GameplayStatics.get_player_controller(game, 0):
                return
            spawners = unreal.GameplayStatics.get_all_actors_of_class(game, unreal.MassSpawner)
            REPORT['spawners'] = [{'actor': a.get_path_name(), 'count': a.get_count(),
                                   'scale': a.get_spawning_count_scale(),
                                   'auto_spawn': a.get_editor_property('auto_spawn_on_begin_play'),
                                   'generators': [r.get_editor_property('generator_instance').get_class().get_name()
                                                  for r in a.get_editor_property('spawn_data_generators')]} for a in spawners]
            REPORT['expected_count'] = round(sum(a.get_count() * a.get_spawning_count_scale() for a in spawners))
            assert REPORT['expected_count'] == 240, REPORT['spawners']
            unreal.SystemLibrary.execute_console_command(game, 't.IdleWhenNotForeground 0')
            REPORT['lighting_survey'] = survey(game)
            save()
            for spawner in spawners:
                spawner.wait_for_streaming_assets()
            S.update(phase='warm', started=time.monotonic(), game_start=unreal.GameplayStatics.get_time_seconds(game),
                     deadline=time.monotonic() + 1200)
            save()
            return
        if unreal.GameplayStatics.is_game_paused(game) or unreal.GameplayStatics.get_global_time_dilation(game) != 1.:
            finish('Simulation paused or time dilation changed')
            return
        if S['phase'] == 'capture_wait':
            for capture in REPORT['captures']:
                path = Path(capture['path'])
                if not path.exists() or path.stat().st_mtime < capture['requested']-1:
                    return
                blob = path.read_bytes()
                assert blob[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', blob[16:24]) == (1280, 800)
                capture['dimensions'] = [1280, 800]
            finish()
            return
        if S['phase'] == 'warm':
            if game_time - S['game_start'] < 10 or now - S['started'] < 15:
                return
            if REPORT['observer'] == 'near' and not S.get('observer_set'):
                entities = unreal.CarnivalCrowdEditorLibrary.sample_live_crowd_entities(game)
                if not entities:
                    return
                point = entities[0].location
                cameras = [a for a in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.CameraActor)
                           if a.get_actor_label() == 'CrowdMovementObserver']
                assert len(cameras) == 1
                camera = cameras[0]
                location = point + unreal.Vector(0, -500, 400)
                camera.set_actor_location(location, False, True)
                camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, point), True)
                unreal.GameplayStatics.get_player_controller(game, 0).set_view_target_with_blend(camera, 0)
                REPORT['observer_location_cm'] = list(location.to_tuple())
                S.update(observer_set=True, game_start=game_time, started=now)
                save()
                return
            REPORT['mass_diagnostics'] = list(unreal.CarnivalCrowdEditorLibrary.describe_live_mass_simulation(game))
            if REPORT['observer'] == 'near':
                assert any(line.startswith(('CrowdLOD=0 ', 'CrowdLOD=1 ', 'CrowdLOD=2 '))
                           for line in REPORT['mass_diagnostics']), 'Near observer did not activate any visible crowd LOD'
            pawn = unreal.GameplayStatics.get_player_pawn(game, 0)
            REPORT['player_location_cm'] = list(pawn.get_actor_location().to_tuple()) if pawn else None
            sample(game)
            request_capture(game, 'NearCrowdStart')
            S.update(phase='measure', measure_start=game_time, next_sample=game_time + 1, deadline=now + 600)
            save()
            return
        if game_time < S['next_sample']:
            return
        sample(game)
        S['next_sample'] = game_time + 1
        if game_time - S['measure_start'] >= 40:
            evaluate()
            if REPORT['capture_enabled']:
                request_capture(game, 'NearCrowdEnd')
                S.update(phase='capture_wait', deadline=now+30)
                save()
            else:
                finish()
    except Exception:
        finish(traceback.format_exc())
    finally:
        S['busy'] = False


save()
entry = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in ('Editor.AsyncAssetCompilationMaxConcurrency 1',
                'Editor.AsyncStaticMeshCompilationMaxConcurrency 1',
                'Editor.AsyncSkinnedAssetCompilationMaxConcurrency 1',
                'Editor.AsyncTextureCompilationMaxConcurrency 1',
                'Editor.AsyncAssetCompilationMaxMemoryUsage 4'):
    unreal.SystemLibrary.execute_console_command(entry, command)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
assert REPORT['observer'] in ('arrival', 'near')
if REPORT['observer'] == 'near':
    camera = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor, unreal.Vector())
    camera.set_actor_label('CrowdMovementObserver')
handle = unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
