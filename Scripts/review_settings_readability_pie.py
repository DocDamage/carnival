"""Capture real HUD settings/remapping at fixed review resolutions.

Uses production menu-opening APIs, not physical or simulated input. Existing
saved preferences are loaded normally and never modified by this script.
"""
import json
import struct
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT/'Saved/PresentationAcceptance/SettingsReadability'
OUT.mkdir(parents=True, exist_ok=True)
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT = {'success':False, 'captures':[], 'errors':[], 'physical_input':False,
          'input_method':'Production ToggleSettingsMenu/OpenControlRemapping API calls',
          'settings_modified':False, 'visual_review':'pending screenshot inspection'}
SHOTS = [('Settings_1280x800',1280,800,'settings'),
         ('Settings_800x600',800,600,'settings'),
         ('Settings_640x480',640,480,'settings'),
         ('Keyboard_remapping_800x600',800,600,'keyboard'),
         ('Gamepad_remapping_800x600',800,600,'gamepad'),
         ('Gamepad_remapping_640x480',640,480,'gamepad')]
STATE = {'phase':'setup','index':0,'deadline':time.monotonic()+180,'busy':False}


def save():
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))


def finish(error=None):
    if error: REPORT['errors'].append(error)
    REPORT['success'] = not REPORT['errors'] and len(REPORT['captures']) == len(SHOTS)
    save()
    LE.editor_request_end_play()
    STATE.update(phase='exit',deadline=time.monotonic()+4)


def tick(_):
    if STATE['busy']: return
    STATE['busy']=True
    try:
        now=time.monotonic()
        if STATE['phase']=='exit':
            if now>STATE['deadline']:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if now>STATE['deadline']:
            finish('Timeout during '+STATE['phase']); return
        world=unreal.EditorLevelLibrary.get_game_world()
        if not world: return
        if STATE['phase']=='setup':
            pc=unreal.GameplayStatics.get_player_controller(world,0)
            if not isinstance(pc,unreal.CarnivalPlayerController) or not pc.get_hud(): return
            if not isinstance(pc.get_hud(),unreal.CarnivalHUD):
                finish('Expected production CarnivalHUD'); return
            unreal.SystemLibrary.execute_console_command(world,'t.IdleWhenNotForeground 0')
            pc.set_control_rotation(unreal.Rotator(pitch=-5,yaw=90,roll=0))
            pc.toggle_settings_menu()
            STATE.update(pc=pc,phase='menu',deadline=now+180)
            return
        pc=STATE['pc']
        name,width,height,menu=SHOTS[STATE['index']]
        image=OUT/(name+'.png')
        if STATE['phase']=='menu':
            if menu!='settings': pc.open_control_remapping(menu=='gamepad')
            STATE.update(phase='settle',ready=now+3)
        elif STATE['phase']=='settle' and now>=STATE['ready']:
            # HighResShot renders the game canvas at these dimensions, including
            # the production AHUD; no image resizing or compositing is performed.
            unreal.SystemLibrary.execute_console_command(world,
                f'HighResShot {width}x{height} filename="{image.as_posix()}"')
            STATE.update(phase='capture',requested=time.time())
        elif STATE['phase']=='capture':
            if not image.exists() or image.stat().st_mtime<STATE['requested']-1 or image.stat().st_size<1000: return
            data=image.read_bytes()
            if data[:8]!=b'\x89PNG\r\n\x1a\n':
                finish('Expected PNG screenshot: '+str(image)); return
            actual=struct.unpack('>II',data[16:24])
            if actual!=(width,height):
                finish(f'Screenshot dimensions {actual} differ from requested {(width,height)}'); return
            REPORT['captures'].append({'image':str(image),'resolution':[width,height],'menu':menu,
                'hud_class':pc.get_hud().get_class().get_name(),'settings_source':'Existing saved user preferences'})
            save(); STATE['index']+=1
            if STATE['index']==len(SHOTS): finish()
            else: STATE.update(phase='menu')
    except Exception:
        finish(traceback.format_exc())
    finally:
        STATE['busy']=False


world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB')
assert world
unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
    unreal.PlayerStart,unreal.Vector(1050,400,140))
handle=unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
