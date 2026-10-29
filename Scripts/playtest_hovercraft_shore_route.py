"""Normal-speed saved hovercraft route from dock to river and back.

Initial on-foot placement only; actual contextual mount, powered movement,
stationary steering, ordinary unload. No fixtures or level saves. Excludes
the crowd. Does not establish rendered appearance or physical-controller use.
"""
import hashlib
import json
import math
import os
import time
import traceback
from pathlib import Path

import unreal

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/WorldExpansion/WaterVehicleAcceptance'
PREFIX = os.environ.get('CARNIVAL_HOVER_ROUTE_REPORT', 'HovercraftShoreRoute_20261029_v5')
ACTIVITY = os.environ.get('CARNIVAL_HOVER_ROUTE_ACTIVITY', '1') == '1'
REPORT = OUT / (PREFIX + '.json')
V = unreal.Vector
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
PATH = [(-57000, -52000, 735), (-57000, -48100, 735), (-50300, -48100, 735),
        (-50300, -54500, 735), (-50300, -55000, 735), (-50300, -57200, -110),
        (-50300, -57650, -110), (-49700, -57650, -110),
        (-49700, -58500, -140), (-47700, -58500, -140)]
ROUTE = PATH[1:] + list(reversed(PATH[:-1]))
R = {'success': False, 'errors': [], 'events': [], 'samples': [], 'excluded_spawners': [],
     'scope': __doc__, 'path_cm': ROUTE, 'time_dilation': 1, 'normal_speed': True}
S = {'phase': 'setup', 'busy': False, 'deadline': time.monotonic() + 360}


def save():
    R['phase'] = S['phase']
    R['updated_epoch'] = time.time()
    temporary = REPORT.with_suffix('.tmp')
    temporary.write_text(json.dumps(R, indent=2))
    temporary.replace(REPORT)


def event(name, **details):
    R['events'].append({'name': name, 'game_seconds': S.get('gt'), **details})
    save()


def finish(error=None):
    if error:
        R['errors'].append(error)
        if S.get('craft'):
            try:
                craft = S['craft']
                p = craft.get_actor_location()
                raw = unreal.SystemLibrary.box_trace_single_by_profile(S['game'], p,
                    p + craft.get_actor_forward_vector() * 100,
                    craft.get_editor_property('collision_box').get_scaled_box_extent(), craft.get_actor_rotation(),
                    'Vehicle', False, [craft, S['player']], unreal.DrawDebugTrace.NONE, True)
                h = raw.to_tuple() if raw else None
                R['failure_collision'] = {'position_cm': p.to_tuple(),
                    'blocker': h[9].get_path_name() if h and h[0] and h[9] else None,
                    'impact_cm': h[5].to_tuple() if h and h[0] else None}
            except Exception:
                R['failure_capture_error'] = traceback.format_exc()
    if S.get('craft'):
        S['craft'].clear_control_inputs()
    R['success'] = not R['errors'] and R.get('walked_after_unload', False) and (not ACTIVITY or R.get('activity_reset_and_replay', False))
    S.update(phase='exit', deadline=time.monotonic() + 4)
    try:
        save()
    finally:
        LE.editor_request_end_play()


def angle(a):
    return (a + 180) % 360 - 180


def next_target():
    S.update(phase='turn', deadline=time.monotonic() + 90)
    S['segment_start'] = S['craft'].get_actor_location()


def tick(_):
    if S['busy']:
        return
    S['busy'] = True
    try:
        wall = time.monotonic()
        if S['phase'] == 'exit':
            if wall >= S['deadline']:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if wall >= S['deadline']:
            raise RuntimeError('Timeout in ' + S['phase'])
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        gt = unreal.GameplayStatics.get_time_seconds(game)
        S['gt'] = gt
        if S['phase'] == 'setup':
            player = unreal.GameplayStatics.get_player_pawn(game, 0)
            if not isinstance(player, unreal.CarnivalPlayerCharacter):
                return
            craft = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.CarnivalHovercraft)
                         if a.get_actor_label() == 'Hovercraft_NorthDock_Handling')
            pc = player.get_controller()
            pc.set_ignore_move_input(False)
            unreal.GameplayStatics.set_game_paused(game, False)
            unreal.GameplayStatics.set_global_time_dilation(game, 1)
            unreal.SystemLibrary.execute_console_command(game, 't.IdleWhenNotForeground 0')
            player.get_movement_component().stop_movement_immediately()
            half = player.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height()
            assert player.set_actor_location(V(-56695, -52750, 635 + half + 3), False, True)
            S.update(game=game, player=player, craft=craft, pc=pc, half=half,
                     phase='approach', ready=gt + 1, deadline=wall + 60, last_sample=-10)
            if ACTIVITY:
                activity = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.CarnivalActivityBase)
                    if a.get_actor_label() == 'Hovercraft_NorthDock_Handling_HandlingActivity')
                checkpoints = activity.get_editor_property('checkpoints')
                assert len(checkpoints) == len(ROUTE), 'Shore course missing from saved map'
                assert all((cp.get_editor_property('location') - V(*point)).length() < .1 for cp, point in zip(checkpoints, ROUTE))
                S['activity'] = activity
                R['activity_checkpoint_count'] = len(checkpoints)
            event('initial_on_foot_placement')
            return
        player, craft = S['player'], S['craft']
        if S['phase'] == 'approach':
            if gt < S['ready']:
                return
            if ACTIVITY and not S.get('activity_started'):
                player.try_context_interact()
                assert S['activity'].get_editor_property('activity_state') == unreal.CarnivalActivityState.ACTIVE
                assert player.get_editor_property('active_activity') == S['activity']
                S['activity_started'] = True
                event('activity_started_through_context')
            pos = player.get_actor_location()
            d = V(-56695, -52000, pos.z) - pos
            if d.length() > 15:
                player.add_movement_input(d.normal(), 1, True)
                return
            player.consume_movement_input_vector()
            player.get_movement_component().stop_movement_immediately()
            assert craft.can_mount(player), 'Cannot mount at the accepted pier approach'
            player.try_interact_or_mount()
            S.update(phase='mount', ready=gt + .5)
            return
        if S['phase'] == 'mount':
            if gt < S['ready']:
                return
            assert unreal.GameplayStatics.get_player_pawn(game, 0) == craft and craft.get_editor_property('current_rider') == player
            S.update(index=0, last_position=craft.get_actor_location())
            event('mounted', at_cm=craft.get_actor_location().to_tuple())
            next_target()
            return
        if S['phase'] in ('turn', 'turn_settle', 'drive', 'brake'):
            if ACTIVITY:
                assert S['activity'].get_editor_property('activity_state') != unreal.CarnivalActivityState.FAILED, 'Course timer expired'
            assert unreal.GameplayStatics.get_player_pawn(game, 0) == craft and craft.get_editor_property('current_rider') == player, 'Lost rider/possession'
            pos = craft.get_actor_location()
            target = V(*ROUTE[S['index']])
            distance = math.hypot(target.x - pos.x, target.y - pos.y)
            yaw = math.degrees(math.atan2(target.y - pos.y, target.x - pos.x))
            error = angle(yaw - craft.get_actor_rotation().yaw)
            speed = abs(craft.get_editor_property('current_forward_speed')) + abs(craft.get_editor_property('current_strafe_speed'))
            assert (pos - S['last_position']).length() < 700, 'Unexpected teleport/recovery'
            S['last_position'] = pos
            assert pos.z > min(S['segment_start'].z, target.z) - 180, 'Craft fell below expected route support'
            if gt - S['last_sample'] > .5:
                R['samples'].append({'seconds': gt, 'phase': S['phase'], 'index': S['index'],
                    'position_cm': pos.to_tuple(), 'rotation': str(craft.get_actor_rotation()), 'speed_cm_s': speed})
                S['last_sample'] = gt
                save()
            if S['phase'] == 'turn':
                craft.input_throttle(0)
                craft.input_steering(max(-.4, min(.4, error / 30)))
                if abs(error) < 1.5 and speed < 5:
                    craft.clear_control_inputs()
                    S.update(phase='turn_settle', ready=gt + .5)
                return
            if S['phase'] == 'turn_settle':
                if gt >= S['ready']:
                    S.update(phase='drive', deadline=wall + 100, progress=pos, progress_at=gt)
                return
            if S['phase'] == 'brake':
                craft.clear_control_inputs()
                if speed < 5:
                    height_error = pos.z - target.z
                    assert abs(height_error) < 60, 'Waypoint reached at wrong support height: ' + str(height_error)
                    event('waypoint', index=S['index'], at_cm=pos.to_tuple(), expected_cm=target.to_tuple(), height_error_cm=height_error)
                    S['index'] += 1
                    if S['index'] == len(ROUTE):
                        craft.dismount()
                        S.update(phase='unload', ready=gt + 1, deadline=wall + 30)
                    else:
                        next_target()
                return
            if distance < 55:
                craft.clear_control_inputs()
                S['phase'] = 'brake'
                return
            if math.hypot(pos.x - S['progress'].x, pos.y - S['progress'].y) > 15:
                S.update(progress=pos, progress_at=gt)
            assert gt - S['progress_at'] < 8, 'Hovercraft stalled at ' + str(pos.to_tuple())
            craft.input_throttle(max(.05, min(.25, distance / 2000)))
            craft.input_steering(max(-.2, min(.2, error / 40)))
            return
        if S['phase'] == 'unload':
            if gt < S['ready']:
                return
            assert unreal.GameplayStatics.get_player_pawn(game, 0) == player and not craft.get_editor_property('current_rider'), 'Ordinary unload failed'
            assert player.get_movement_component().is_moving_on_ground(), 'No grounded exit'
            if ACTIVITY:
                activity = S['activity']
                assert activity.get_editor_property('activity_state') == unreal.CarnivalActivityState.COMPLETED
                assert activity.get_editor_property('current_checkpoint_index') == len(ROUTE)
                assert activity.get_editor_property('current_score') == len(ROUTE) * 100
                event('activity_completed', score=activity.get_editor_property('current_score'),
                      elapsed_seconds=activity.get_editor_property('elapsed_time'))
            event('unloaded', at_cm=player.get_actor_location().to_tuple())
            S.update(phase='walk_after', start=player.get_actor_location())
            return
        if S['phase'] == 'walk_after':
            d = V(-56695, -52750, player.get_actor_location().z) - player.get_actor_location()
            if d.length() > 40:
                player.add_movement_input(d.normal(), 1, True)
            else:
                assert player.get_movement_component().is_moving_on_ground()
                assert (player.get_actor_location() - S['start']).length() > 100
                player.consume_movement_input_vector()
                player.get_movement_component().stop_movement_immediately()
                if ACTIVITY:
                    activity = S['activity']
                    player.try_context_interact()
                    assert activity.get_editor_property('activity_state') == unreal.CarnivalActivityState.INACTIVE
                    assert not player.get_editor_property('active_activity')
                    player.try_context_interact()
                    assert activity.get_editor_property('activity_state') == unreal.CarnivalActivityState.ACTIVE
                    assert activity.get_editor_property('current_checkpoint_index') == 0
                    assert activity.get_editor_property('current_score') == 0
                    activity.abort_activity()
                    assert activity.get_editor_property('activity_state') == unreal.CarnivalActivityState.INACTIVE
                    assert not player.get_editor_property('active_activity')
                    R['activity_reset_and_replay'] = True
                    event('activity_reset_replay_and_abort')
                R['walked_after_unload'] = True
                finish()
    except Exception:
        finish(traceback.format_exc())
    finally:
        S['busy'] = False


try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    ea = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(ea.get_all_level_actors()):
        if actor.get_class().get_name() == 'MetaHumanMassSpawner':
            R['excluded_spawners'].append(actor.get_actor_label())
            ea.destroy_actor(actor)
    R['map_sha256'] = hashlib.sha256((ROOT / 'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout.umap').read_bytes()).hexdigest()
    save()
    handle = unreal.register_slate_post_tick_callback(tick)
    LE.editor_request_begin_play()
except Exception:
    R['errors'].append(traceback.format_exc())
    save()
    unreal.SystemLibrary.quit_editor()
