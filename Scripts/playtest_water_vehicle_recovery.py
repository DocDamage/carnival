"""Real saved water vehicles: blocked manual recovery and unsupported fall recovery.

Initial on-foot placement per vehicle and an explicit far-away hovercraft
displacement are failure-injection fixtures. Challenges start through the API
to verify cancellation on recovery. Controls, possession, ordinary unloading
and resumed walking use the real gameplay systems. No map saves or crowd.
Optional connected-world UI captures retain saved exposure/fog/lighting.
The explicit dock_only scene uses fixture lighting and excludes the wider world.
"""
import json
import gc
import os
import time
import traceback
from pathlib import Path

import unreal

ROOT = Path(r'F:\Carnival')
PREFIX = os.environ.get('CARNIVAL_RECOVERY_REPORT', 'WaterVehicleRecovery_20261029_v1')
OUT = ROOT / 'Saved/WorldExpansion/WaterVehicleAcceptance' / PREFIX
OUT.mkdir(parents=True, exist_ok=False)
CAPTURE = os.environ.get('CARNIVAL_RECOVERY_RENDER') == '1'
DOCK_ONLY = os.environ.get('CARNIVAL_RECOVERY_SCENE') == 'dock_only'
V = unreal.Vector
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
CASES = [('boat', 'Boat_NorthDock_Inflatable', (-49274, -57200, -210)),
         ('hovercraft', 'Hovercraft_NorthDock_Handling', (-56695, -52000, 635))]
R = {'success': False, 'errors': [], 'cases': [], 'captures': [], 'excluded_spawners': [],
     'scope': __doc__, 'visual_review': 'pending' if CAPTURE else 'not rendered',
     'scene': 'isolated saved North Dock with fixture lighting' if DOCK_ONLY else 'connected world',
     'full_world_visual_acceptance': False, 'physical_input': False, 'assets_saved': False}
S = {'phase': 'setup', 'busy': False, 'deadline': time.monotonic() + 600, 'index': 0}


def save():
    R['phase'] = S['phase']
    p = OUT / 'index.tmp'
    p.write_text(json.dumps(R, indent=2))
    p.replace(OUT / 'index.json')


def finish(error=None):
    if error:
        R['errors'].append(error)
    if S.get('vehicle'):
        S['vehicle'].clear_control_inputs()
    R['success'] = not R['errors'] and len(R['cases']) == 2 and all(c.get('ordinary_exit') and c.get('recovery_pass')
        and (c['kind'] != 'hovercraft' or c.get('brake_pass')) for c in R['cases'])
    S.update(phase='exit', deadline=time.monotonic() + 4)
    try:
        save()
    finally:
        LE.editor_request_end_play()


def capture(name, next_phase):
    if not CAPTURE:
        S['phase'] = next_phase
        return
    variants = [(1280, 800, False), (640, 480, True)]
    if name == 'boat_recovery_available':
        variants += [(640, 480, False), (1280, 800, True)]
    S.update(phase='capture_viewport', capture_name=name, after_capture=next_phase,
             capture_variants=variants, capture_index=0, capture_ready=S['gt'] + 1)
    S['pc'].set_editor_property('using_gamepad', variants[0][2])
    assert unreal.CarnivalRouteEditorLibrary.set_game_viewport_size(S['game'], unreal.IntPoint(*variants[0][:2]))


def place_case():
    kind, label, location = CASES[S['index']]
    game, player = S['game'], S['player']
    cls = unreal.CarnivalBoat if kind == 'boat' else unreal.CarnivalHovercraft
    vehicle = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game, cls) if a.get_actor_label() == label)
    activity = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.CarnivalActivityBase)
                    if a.get_actor_label() == label + '_HandlingActivity')
    player.get_movement_component().stop_movement_immediately()
    assert player.set_actor_location(V(*location) + V(0, 0, S['half'] + 3), False, True)
    player.get_movement_component().set_movement_mode(unreal.MovementMode.MOVE_FALLING)
    S['pc'].set_control_rotation(unreal.Rotator(yaw=vehicle.get_actor_rotation().yaw, pitch=-12))
    S.update(vehicle=vehicle, activity=activity, phase='settle', ready=S['gt'] + 1,
             deadline=time.monotonic() + 240, last_sample=-10)
    record = {'kind': kind, 'vehicle': label, 'samples': []}
    R['cases'].append(record)
    save()


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
        assert wall < S['deadline'], 'Timeout in ' + S['phase']
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        gt = unreal.GameplayStatics.get_time_seconds(game)
        S['gt'] = gt
        if S['phase'] == 'setup':
            player = unreal.GameplayStatics.get_player_pawn(game, 0)
            if not isinstance(player, unreal.CarnivalPlayerCharacter):
                return
            S.update(game=game, player=player, pc=player.get_controller(),
                     half=player.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height())
            unreal.GameplayStatics.set_game_paused(game, False)
            unreal.GameplayStatics.set_global_time_dilation(game, 1)
            unreal.SystemLibrary.execute_console_command(game, 't.IdleWhenNotForeground 0')
            S['pc'].set_ignore_move_input(False)
            if CAPTURE and DOCK_ONLY:
                instance = unreal.GameplayStatics.get_game_instance(game)
                mission = next(o for o in unreal.ObjectIterator(unreal.CarnivalMissionSubsystem) if o.get_outer() == instance)
                assert mission.begin_story_mission()
                R['story_overlay_fixture'] = True
            if CAPTURE:
                assert isinstance(S['pc'].get_hud(), unreal.CarnivalHUD), 'Gameplay HUD missing'
                R['hud_class'] = S['pc'].get_hud().get_class().get_name()
            R['directional_lights'] = [{'actor': a.get_actor_label(), 'level': a.get_level().get_path_name(),
                'intensity': a.get_component_by_class(unreal.DirectionalLightComponent).get_editor_property('intensity')}
                for a in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.DirectionalLight)]
            place_case()
            return
        vehicle, player, activity = S['vehicle'], S['player'], S['activity']
        record = R['cases'][-1]
        if S['phase'] == 'capture_viewport':
            if gt < S['capture_ready']:
                return
            width, height, gamepad = S['capture_variants'][S['capture_index']]
            device = 'gamepad' if gamepad else 'keyboard'
            target = OUT / (S['capture_name'] + '_' + device + '_' + str(width) + 'x' + str(height) + '.png')
            size = unreal.CarnivalRouteEditorLibrary.capture_game_viewport_png(game, str(target))
            assert size.x == width and size.y == height and target.exists(), 'Actual game viewport capture failed'
            R['captures'].append({'image': str(target), 'stage': S['capture_name'], 'resolution': [width, height], 'prompts': device,
                'camera_cm': unreal.GameplayStatics.get_player_camera_manager(game, 0).get_camera_location().to_tuple()})
            S['capture_index'] += 1
            if S['capture_index'] < len(S['capture_variants']):
                variant = S['capture_variants'][S['capture_index']]
                S['pc'].set_editor_property('using_gamepad', variant[2])
                assert unreal.CarnivalRouteEditorLibrary.set_game_viewport_size(game, unreal.IntPoint(*variant[:2]))
                S['capture_ready'] = gt + 1
            else:
                S['pc'].set_editor_property('using_gamepad', False)
                S['phase'] = S['after_capture']
            save()
            return
        if S['phase'] == 'settle':
            if gt < S['ready']:
                return
            assert player.get_movement_component().is_moving_on_ground()
            assert vehicle.can_mount(player), 'Accepted boarding marker is no longer valid'
            S['boarding'] = vehicle.get_actor_location()
            player.try_interact_or_mount()
            S.update(phase='mounted', ready=gt + 2)
            return
        if S['phase'] == 'mounted':
            if gt < S['ready']:
                return
            assert unreal.GameplayStatics.get_player_pawn(game, 0) == vehicle and vehicle.get_editor_property('current_rider') == player
            context = S['pc'].get_editor_property('motorcycle_mapping_context')
            mappings = [(m.action, str(m.key.get_editor_property('key_name')))
                        for m in context.get_editor_property('default_key_mappings').get_editor_property('mappings')]
            required = [(S['pc'].get_editor_property('context_interact_action'), key)
                        for key in ('E', 'Gamepad_DPad_Right')]
            required += [(S['pc'].get_editor_property('cancel_action'), key)
                         for key in ('BackSpace', 'Gamepad_FaceButton_Right')]
            assert all(pair in mappings for pair in required), 'Mounted course input bindings missing'
            record['mounted_activity_bindings'] = [{'action': action.get_name(), 'key': key} for action, key in required]
            boom = vehicle.get_editor_property('camera_boom')
            camera = vehicle.get_editor_property('follow_camera')
            assert (camera.get_world_location() - vehicle.get_actor_location()).length() > 200, 'Mounted camera collapsed to vehicle origin'
            record['mounted_camera'] = {
                'arm_length': boom.get_editor_property('target_arm_length'),
                'socket_offset': boom.get_editor_property('socket_offset').to_tuple(),
                'target_offset': boom.get_editor_property('target_offset').to_tuple(),
                'relative_location': boom.get_editor_property('relative_location').to_tuple(),
                'collision_test': boom.get_editor_property('do_collision_test'),
                'camera_active': camera.is_active(),
                'camera_location_cm': camera.get_world_location().to_tuple(),
                'vehicle_location_cm': vehicle.get_actor_location().to_tuple()}
            if DOCK_ONLY:
                start = boom.get_world_location() + boom.get_editor_property('target_offset')
                rotation = S['pc'].get_control_rotation()
                end = (start - unreal.MathLibrary.get_forward_vector(rotation) * boom.get_editor_property('target_arm_length')
                    + unreal.MathLibrary.rotate_angle_axis(boom.get_editor_property('socket_offset'), rotation.yaw, V(0, 0, 1)))
                record['camera_probe'] = []
                for ignored in ([vehicle], [vehicle, player]):
                    result = unreal.SystemLibrary.sphere_trace_single(game, start, end, boom.get_editor_property('probe_size'),
                        unreal.TraceTypeQuery.ECC_CAMERA, False, ignored, unreal.DrawDebugTrace.NONE, True)
                    hit = result.to_tuple() if result else None
                    record['camera_probe'].append({'ignore_rider': len(ignored) == 2,
                        'blocked': bool(hit and hit[0]), 'initial_overlap': bool(hit and hit[1]),
                        'actor': hit[9].get_actor_label() if hit and hit[9] else None,
                        'component': hit[10].get_name() if hit and hit[10] else None})
            activity.start_activity(player)
            record['boarding_cm'] = S['boarding'].to_tuple()
            capture(record['kind'] + '_mounted_course', 'inject' if record['kind'] == 'boat' else 'brake_drive')
            return
        if S['phase'] == 'brake_drive':
            vehicle.input_throttle(.25)
            vehicle.input_strafe(.25)
            S.update(phase='brake_motion', ready=gt + .5)
            return
        if S['phase'] == 'brake_motion':
            if gt < S['ready']:
                return
            assert vehicle.get_editor_property('current_forward_speed') > 100
            assert vehicle.get_editor_property('current_strafe_speed') > 100
            vehicle.input_brake(1)
            S.update(phase='brake_hold', ready=gt + 2)
            return
        if S['phase'] == 'brake_hold':
            if gt < S['ready']:
                return
            assert abs(vehicle.get_editor_property('current_forward_speed')) < 1
            assert abs(vehicle.get_editor_property('current_strafe_speed')) < 1
            assert not vehicle.can_recover_to_boarding_point(), 'Braking was misclassified as stuck'
            vehicle.input_brake(0)
            S.update(phase='brake_release', ready=gt + .3)
            return
        if S['phase'] == 'brake_release':
            if gt < S['ready']:
                return
            assert vehicle.get_editor_property('current_forward_speed') > 100
            assert vehicle.get_editor_property('current_strafe_speed') > 100
            record['brake_pass'] = True
            vehicle.clear_control_inputs()
            S['phase'] = 'inject'
            return
        if S['phase'] == 'inject':
            if record['kind'] == 'boat':
                vehicle.input_throttle(.5)
                S.update(phase='blocked', started=gt)
            else:
                assert vehicle.set_actor_location(V(1000000, 1000000, 1700), False, True)
                vehicle.input_throttle(.3)
                vehicle.input_strafe(.3)
                vehicle.input_boost(True)
                S.update(phase='fall', started=gt)
            return
        if S['phase'] in ('blocked', 'fall'):
            assert unreal.GameplayStatics.get_player_pawn(game, 0) == vehicle and vehicle.get_editor_property('current_rider') == player
            pos = vehicle.get_actor_location()
            if gt - S['last_sample'] > .25:
                record['samples'].append({'seconds': gt - S['started'], 'position_cm': pos.to_tuple(),
                    'can_recover': bool(vehicle.can_recover_to_boarding_point())})
                S['last_sample'] = gt
                save()
            assert gt - S['started'] < 20, 'Recovery did not complete'
            if S['phase'] == 'blocked' and vehicle.can_recover_to_boarding_point():
                record['manual_prompt_available'] = True
                capture('boat_recovery_available', 'manual_recover')
            elif S['phase'] == 'fall' and (pos - S['boarding']).length() < 3:
                record['automatic_return'] = True
                S.update(phase='recovered', ready=gt + 1)
            return
        if S['phase'] == 'manual_recover':
            vehicle.dismount()
            assert (vehicle.get_actor_location() - S['boarding']).length() < .1
            S.update(phase='recovered', ready=gt + 1)
            return
        if S['phase'] == 'recovered':
            if gt < S['ready']:
                return
            assert unreal.GameplayStatics.get_player_pawn(game, 0) == vehicle and vehicle.get_editor_property('current_rider') == player
            pos = vehicle.get_actor_location()
            assert (pos - S['boarding']).length() < 30
            assert activity.get_editor_property('activity_state') == unreal.CarnivalActivityState.INACTIVE
            assert not player.get_editor_property('active_activity')
            assert not vehicle.can_recover_to_boarding_point()
            if record['kind'] == 'boat':
                assert abs(vehicle.get_editor_property('current_speed')) < 1
            else:
                assert not vehicle.get_editor_property('is_boosting')
                assert abs(vehicle.get_editor_property('current_forward_speed')) < 1
                assert abs(vehicle.get_editor_property('current_strafe_speed')) < 1
            record.update(recovery_pass=True, recovered_cm=pos.to_tuple(), active_challenge_cancelled=True)
            vehicle.dismount()
            S.update(phase='exit_check', ready=gt + 1)
            return
        if S['phase'] == 'exit_check':
            if gt < S['ready']:
                return
            assert unreal.GameplayStatics.get_player_pawn(game, 0) == player
            assert player.get_movement_component().is_moving_on_ground()
            record['ordinary_exit'] = True
            if S['index'] == len(CASES) - 1:
                finish()
            else:
                S['index'] += 1
                place_case()
    except Exception:
        finish(traceback.format_exc())
    finally:
        S['busy'] = False


try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    ea = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if DOCK_ONLY:
        world = unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
        assert world
        world.get_world_settings().set_editor_property('default_game_mode', unreal.load_class(
            None, '/Game/Carnival/Blueprints/BP_CarnivalGameMode.BP_CarnivalGameMode_C'))
        stream = unreal.EditorLevelUtils.add_level_to_world_with_transform(world,
            '/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout',
            unreal.LevelStreamingAlwaysLoaded, unreal.Transform(location=V(-55000, -55000, 600)))
        assert stream
        ea.spawn_actor_from_class(unreal.PlayerStart, V(-56695, -52000, 735))
        light = ea.spawn_actor_from_class(unreal.DirectionalLight, V(-54000, -53000, 2500),
            unreal.Rotator(pitch=-45, yaw=-65))
        light.set_actor_label('RecoveryReview_FixtureLight')
        light.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity', 2.)
        R['limits'] = ('Saved dock geometry/vehicles and real gameplay HUD/controller only. Surrounding world, '
            'landscape, river rendering, saved lighting/fog, crowd and performance are excluded. '
            'Fixture light is temporary; this does not accept normal connected-world presentation.')
    else:
        assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    for actor in list(ea.get_all_level_actors()):
        if actor.get_class().get_name() == 'MetaHumanMassSpawner':
            R['excluded_spawners'].append(actor.get_actor_label())
            ea.destroy_actor(actor)
    gc.collect()
    R['deleted_authoring_memory_released_bytes'] = unreal.CarnivalRouteEditorLibrary.purge_authoring_undo_for_review()
    save()
    handle = unreal.register_slate_post_tick_callback(tick)
    LE.editor_request_begin_play()
except Exception:
    R['errors'].append(traceback.format_exc())
    save()
    unreal.SystemLibrary.quit_editor()
