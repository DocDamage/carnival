"""Walk each eastern basin pocket to the quay and back in normal-speed PIE.

Initial placement per pocket is a test fixture. Each round trip thereafter
uses ordinary movement, without jumping, recovery or intermediate teleports.
No map is saved; the crowd spawner is excluded for this geometry check.
"""
import json
import math
import time
import traceback
from pathlib import Path

import unreal

OUT = Path(r'F:\Carnival\Saved\WorldExpansion\EastDockBasinReturnsPIE_20261029.json')
V = unreal.Vector
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
CASES = [
    ('inner_east', [(72300, 20100, 560), (72300, 19900, 560), (72300, 18500, 645)]),
    ('outer_east', [(73700, 25000, 560), (73700, 20100, 560), (73700, 18500, 645)]),
]
R = {'success': False, 'errors': [], 'tests': [], 'excluded_spawners': [],
     'scope': __doc__, 'time_dilation': 1, 'expected_return_slipways': 2}
S = {'phase': 'setup', 'busy': False, 'deadline': time.monotonic() + 360}


def save():
    pending = OUT.with_suffix('.tmp')
    pending.write_text(json.dumps(R, indent=2))
    pending.replace(OUT)


def finish(error=None):
    if error:
        R['errors'].append(error)
    if S.get('player'):
        S['player'].get_movement_component().stop_movement_immediately()
        S['player'].consume_movement_input_vector()
    R['success'] = not R['errors'] and len(R['tests']) == 4 and all(t['success'] for t in R['tests'])
    R['finished_epoch'] = time.time()
    S.update(phase='exit', deadline=time.monotonic() + 4)
    try:
        save()
    finally:
        LE.editor_request_end_play()


def place_case():
    name, path = CASES[S['case']]
    player = S['player']
    player.get_movement_component().stop_movement_immediately()
    assert player.set_actor_location(V(*path[0]) + V(0, 0, S['half'] + 4), False, True)
    S.update(phase='settle', settle_until=S['game_time'] + 1, deadline=time.monotonic() + 100)


def start_leg(reverse=False):
    name, path = CASES[S['case']]
    if reverse:
        path = list(reversed(path))
    record = {'name': name + ('_return' if reverse else '_outbound'), 'success': False,
              'start_cm': S['player'].get_actor_location().to_tuple(), 'samples': []}
    R['tests'].append(record)
    S.update(phase='walk', path=path, index=1, reverse=reverse, start=S['game_time'],
             progress_time=S['game_time'], progress_index=1, previous_position=S['player'].get_actor_location(),
             last_sample=-10, deadline=time.monotonic() + 100)
    save()


def tick(_):
    if S['busy']:
        return
    S['busy'] = True
    try:
        if S['phase'] == 'exit':
            if time.monotonic() >= S['deadline']:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if time.monotonic() >= S['deadline']:
            raise RuntimeError('Wall timeout in ' + S['phase'])
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        unreal.GameplayStatics.set_game_paused(game, False)
        gt = unreal.GameplayStatics.get_time_seconds(game)
        S['game_time'] = gt
        if S['phase'] == 'setup':
            player = unreal.GameplayStatics.get_player_pawn(game, 0)
            if not isinstance(player, unreal.CarnivalPlayerCharacter):
                return
            S.update(player=player, game=game, case=0,
                     half=player.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height())
            player.get_controller().set_ignore_move_input(False)
            unreal.GameplayStatics.set_global_time_dilation(game, 1)
            unreal.SystemLibrary.execute_console_command(game, 't.IdleWhenNotForeground 0')
            ramps = unreal.GameplayStatics.get_all_actors_with_tag(game, 'CarnivalBasinReturn')
            R['return_slipways_in_game'] = [a.get_actor_label() for a in ramps]
            assert len(ramps) == 2, 'Saved return slipways missing'
            R['player_class'] = player.get_class().get_name()
            R['capsule_half_height_cm'] = S['half']
            place_case()
            return
        player = S['player']
        move = player.get_movement_component()
        pos = player.get_actor_location()
        if S['phase'] == 'settle':
            if gt >= S['settle_until']:
                assert move.is_moving_on_ground(), 'Initial basin placement did not settle'
                assert abs(pos.z - S['half'] - CASES[S['case']][1][0][2]) < 12, 'Wrong initial floor'
                start_leg()
            return
        current = R['tests'][-1]
        target = V(*S['path'][S['index']])
        horizontal = math.hypot(target.x - pos.x, target.y - pos.y)
        assert pos.z > 530 + S['half'], 'Fell below basin floor'
        assert (pos - S['previous_position']).length() < 500, 'Unexpected position discontinuity/recovery'
        S['previous_position'] = pos
        if gt - S['last_sample'] >= .5:
            floor = move.current_floor.hit_result.to_tuple() if move.is_moving_on_ground() else None
            current['samples'].append({'seconds': round(gt - S['start'], 2), 'position_cm': pos.to_tuple(),
                'grounded': bool(move.is_moving_on_ground()), 'floor': floor[9].get_actor_label() if floor and floor[9] else None})
            S['last_sample'] = gt
            save()
        if horizontal < 65:
            if S['index'] < len(S['path']) - 1:
                S['index'] += 1
                S['progress_time'] = gt
                return
            assert move.is_moving_on_ground(), 'Endpoint is not grounded'
            error = pos.z - S['half'] - target.z
            assert abs(error) < 12, 'Endpoint on wrong floor: ' + str(error)
            player.consume_movement_input_vector()
            move.stop_movement_immediately()
            current.update(success=True, seconds=round(gt - S['start'], 2),
                           end_cm=pos.to_tuple(), endpoint_height_error_cm=error)
            if not S['reverse']:
                start_leg(True)
            elif S['case'] + 1 < len(CASES):
                S['case'] += 1
                place_case()
            else:
                finish()
            return
        if gt - S['progress_time'] > 30:
            raise RuntimeError('No waypoint progress for 30 game seconds at ' + str(pos.to_tuple()))
        direction = V(target.x - pos.x, target.y - pos.y, 0).normal()
        player.add_movement_input(direction, 1, True)
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
    save()
    handle = unreal.register_slate_post_tick_callback(tick)
    LE.editor_request_begin_play()
except Exception:
    R['errors'].append(traceback.format_exc())
    save()
    unreal.SystemLibrary.quit_editor()
