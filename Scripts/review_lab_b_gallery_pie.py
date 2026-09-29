"""Walk the saved Lab B gallery with the gameplay pawn and capture its real camera."""
import json
import math
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(r'F:\Carnival')
MAP = '/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB'
OUT = ROOT/'Saved/WorldExpansion/LabB_Gallery_PIE'
OUT.mkdir(parents=True, exist_ok=True)
report = {'success': False, 'map': MAP, 'movement': 'Normal-speed gameplay pawn, continuous out-and-back gallery walk; no physical input.',
          'scope': 'Isolated saved Lab B lighting and real third-person camera; full connected-world arrival remains separate.',
          'walk': [], 'captures': [], 'errors': []}
le = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError('Could not load Lab B')
# This streamed interior has no standalone spawn. Use an unsaved test start so
# the production game mode can create its normal pawn without colliding at zero.
start=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
    unreal.PlayerStart,unreal.Vector(1050.,400.,140.))
start.set_actor_label('Transient_Gallery_Acceptance_Start')
report['unsaved_player_start_fixture']=True
state = {'phase': 'setup', 'deadline': time.monotonic()+120, 'busy': False, 'index': 0}
path = [(820.,400.),(1250.,400.),(1050.,400.)]
views = [('North_gallery',(1050.,744.,195.)),('North_gallery_offset',(850.,744.,195.)),
         ('South_gallery',(1050.,56.,195.)),('South_gallery_offset',(850.,56.,195.))]

def save():
    (OUT/'Review.json').write_text(json.dumps(report, indent=2))

def finish(error=None):
    if error:
        report['errors'].append(error)
    report['success'] = not report['errors'] and len(report['walk']) == len(path) and len(report['captures']) == len(views)
    save()
    le.editor_request_end_play()
    state.update(phase='exit', deadline=time.monotonic()+3)

def tick(delta):
    if state['busy']:
        return
    state['busy'] = True
    try:
        now = time.monotonic()
        if state['phase'] == 'exit':
            if now > state['deadline']:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if now > state['deadline']:
            finish('Timeout during ' + state['phase']); return
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game:
            return
        if state['phase'] == 'setup':
            pawn = unreal.GameplayStatics.get_player_pawn(game,0)
            pc = unreal.GameplayStatics.get_player_controller(game,0)
            if not pawn or not pc:
                return
            if not isinstance(pawn, unreal.CarnivalPlayerCharacter):
                finish('Expected actual Carnival gameplay pawn, got '+pawn.get_class().get_name()); return
            report['player_class'] = pawn.get_class().get_name()
            unreal.GameplayStatics.set_game_paused(game,False)
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
            pawn.set_actor_location(unreal.Vector(1050.,400.,140.),False,True)
            pawn.get_movement_component().stop_movement_immediately()
            pc.set_control_rotation(unreal.Rotator(pitch=-5.,yaw=90.,roll=0.))
            if pc.get_hud(): pc.get_hud().set_editor_property('show_hud',False)
            state.update(pawn=pawn,pc=pc,game=game,phase='settle',ready=now+3,deadline=now+90)
            return
        pawn = state['pawn']; pc = state['pc']; pos = pawn.get_actor_location()
        if pos.z < 75 or pos.z > 220:
            finish('Gallery floor support failed at '+str(pos)); return
        if state['phase'] == 'settle' and now >= state['ready']:
            state.update(phase='walk',leg_started=now,deadline=now+30)
        if state['phase'] == 'walk':
            target = path[state['index']]
            distance = math.hypot(target[0]-pos.x,target[1]-pos.y)
            if distance < 25:
                report['walk'].append({'target': target, 'position': list(pos.to_tuple()), 'seconds': round(now-state['leg_started'],2)})
                state['index'] += 1
                pawn.get_movement_component().stop_movement_immediately()
                save()
                if state['index'] == len(path):
                    state.update(phase='view',index=0,deadline=now+90)
                else:
                    state.update(leg_started=now,deadline=now+30)
                return
            pawn.add_movement_input(unreal.Vector((target[0]-pos.x)/distance,(target[1]-pos.y)/distance,0),1.,True)
        elif state['phase'] == 'view':
            name, target = views[state['index']]
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(pos+unreal.Vector(0,0,55),unreal.Vector(*target)))
            state.update(phase='view_settle',ready=now+5,deadline=now+60)
        elif state['phase'] == 'view_settle' and now >= state['ready']:
            name, target = views[state['index']]
            image = OUT/(name+'.png')
            unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x800 filename="'+image.as_posix()+'"')
            state.update(phase='image',requested=time.time())
        elif state['phase'] == 'image':
            name, target = views[state['index']]
            image = OUT/(name+'.png')
            if image.exists() and image.stat().st_mtime >= state['requested']-1 and image.stat().st_size > 10000:
                manager = unreal.GameplayStatics.get_player_camera_manager(game,0)
                report['captures'].append({'name':name,'image':str(image),'player':list(pos.to_tuple()),
                    'camera':list(manager.get_camera_location().to_tuple()),'target':target})
                state['index'] += 1; save()
                if state['index'] == len(views): finish()
                else: state.update(phase='view',deadline=now+60)
    except Exception:
        finish(traceback.format_exc())
    finally:
        state['busy'] = False

handle = unreal.register_slate_post_tick_callback(tick)
le.editor_request_begin_play()
