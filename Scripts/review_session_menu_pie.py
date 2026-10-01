"""Capture production pause/save UI; native automation separately tests button dispatch.

Uses temporary PIE and API menu state selection. No user saves/preferences/assets
are modified; this is screenshot acceptance, not physical controller acceptance.
"""
import json
import struct
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT/'Saved/PresentationAcceptance/SessionMenu'
OUT.mkdir(parents=True, exist_ok=True)
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT = {'success': False, 'captures': [], 'errors': [], 'physical_input': False,
          'saves_modified': False, 'assets_modified': False,
          'visual_review': 'pending', 'input_method': 'Production ToggleSessionMenu plus temporary selection properties'}
SHOTS = [('Pause_1280x800', 1280, 800, -1), ('Pause_800x600', 800, 600, -1),
         ('Pause_640x480', 640, 480, -1), ('SaveConfirm_640x480', 640, 480, 2),
         ('LoadConfirm_640x480', 640, 480, 3), ('QuitConfirm_640x480', 640, 480, 6)]
S = {'phase': 'setup', 'index': 0, 'deadline': time.monotonic()+240, 'busy': False}

def save():
    (OUT/'index.json').write_text(json.dumps(REPORT, indent=2))

def finish(error=None):
    if error: REPORT['errors'].append(error)
    REPORT['success'] = not REPORT['errors'] and len(REPORT['captures']) == len(SHOTS)
    save()
    LE.editor_request_end_play()
    S.update(phase='exit', deadline=time.monotonic()+4)

def tick(_):
    if S['busy']: return
    S['busy'] = True
    try:
        now = time.monotonic()
        if S['phase'] == 'exit':
            if now > S['deadline']:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if now > S['deadline']:
            finish('Timeout in '+S['phase']); return
        world = unreal.EditorLevelLibrary.get_game_world()
        if not world: return
        if S['phase'] == 'setup':
            pc = unreal.GameplayStatics.get_player_controller(world, 0)
            if not isinstance(pc, unreal.CarnivalPlayerController) or not pc.get_hud(): return
            assert isinstance(pc.get_hud(), unreal.CarnivalHUD)
            REPORT['default_help_overlay'] = pc.get_hud().get_editor_property('show_help_overlay')
            if REPORT['default_help_overlay']:
                finish('Production HUD still enables development overlay by default'); return
            unreal.SystemLibrary.execute_console_command(world, 't.IdleWhenNotForeground 0')
            pc.set_editor_property('using_gamepad', True)
            pc.toggle_session_menu()
            S.update(pc=pc, phase='menu', deadline=now+240)
            return
        name, width, height, confirmation = SHOTS[S['index']]
        image = OUT/(name+'.png')
        if S['phase'] == 'menu':
            S['pc'].set_editor_property('session_menu_selection', 1)
            S['pc'].set_editor_property('session_menu_confirmation', confirmation)
            S.update(phase='settle', ready=now+3)
        elif S['phase'] == 'settle' and now >= S['ready']:
            unreal.SystemLibrary.execute_console_command(world,
                f'HighResShot {width}x{height} filename="{image.as_posix()}"')
            S.update(phase='capture', requested=time.time())
        elif S['phase'] == 'capture':
            if not image.exists() or image.stat().st_mtime < S['requested']-1: return
            data = image.read_bytes()
            assert data[:8] == b'\x89PNG\r\n\x1a\n'
            assert struct.unpack('>II', data[16:24]) == (width, height)
            REPORT['captures'].append({'image': str(image), 'resolution': [width, height],
                                       'confirmation': confirmation})
            save(); S['index'] += 1
            if S['index'] == len(SHOTS): finish()
            else: S.update(phase='menu')
    except Exception:
        finish(traceback.format_exc())
    finally:
        S['busy'] = False

world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB')
assert world
unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
    unreal.PlayerStart, unreal.Vector(1050, 400, 140))
handle = unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
