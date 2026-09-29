"""Capture the saved Lab B art through a PIE camera, with the room's saved lights."""
import json
import os
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(r'F:\Carnival')
MAP = '/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB'
OUT = ROOT / 'Saved/WorldExpansion/LabB_WallArt_PIE'
closeups = os.environ.get('CARNIVAL_ART_CLOSEUPS') == '1'
if closeups: OUT = ROOT / 'Saved/WorldExpansion/LabB_WallArt_Closeups'
lit_closeups = os.environ.get('CARNIVAL_ART_CLOSEUPS_LIT') == '1'
if lit_closeups: OUT = ROOT / 'Saved/WorldExpansion/LabB_WallArt_Closeups_Lit'
orientation_probe = os.environ.get('CARNIVAL_ART_ORIENTATION_PROBE') == '1'
if orientation_probe: OUT = ROOT / 'Saved/WorldExpansion/LabB_WallArt_OrientationProbe'
OUT.mkdir(parents=True, exist_ok=True)
CASES = [('Portraits_West', (-1075., 850., 180.), (-1075., 1445., 180.)),
         ('Portraits_Center', (-375., 850., 180.), (-375., 1445., 180.)),
         ('Photos_East', (325., 850., 180.), (325., 1445., 180.)),
         ('Room_South', (-375., 850., 170.), (-375., -1000., 170.)),
         ('Room_West', (-375., 400., 170.), (-1800., 400., 170.))]
if closeups:
    placements=json.loads((ROOT/'Saved/WorldExpansion/HorrorPaintVol48_LabB_WallArt_Placement.json').read_text())['placements']
    CASES=[(p['label'],(p['bounds_center_cm'][0],p['wall_face_y_cm']-110.,p['bounds_center_cm'][2]),tuple(p['bounds_center_cm'])) for p in placements]
report = {'map': MAP, 'mode': 'Rendered PIE of saved Lab B sublevel, isolated from connected Carnival; saved lights and materials', 'captures': [], 'errors': []}
if closeups: report['mode']='Unlit PIE close-up diagnostics of all eleven frames; cameras may be inside display machinery, so these are not normal-player visibility acceptance.'
if lit_closeups: report['mode']='Saved-lighting PIE close-ups of all eleven frames; cameras may be inside display machinery. No lighting or exposure overrides.'
le = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if orientation_probe:
    report['orientation_probe']='Unsaved: Portrait01/Photo01 translated 20 cm off wall; Portrait02/Photo02 additionally rotated 180 degrees and recentered.'
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label=actor.get_actor_label()
        if label not in ['WorldExpansion_WallArt_LabB_'+s for s in ('Portrait_01','Portrait_02','Photo_01','Photo_02')]: continue
        center,extent=actor.get_actor_bounds(False,True)
        if label.endswith('_02'):
            rot=actor.get_actor_rotation(); rot.yaw+=180.
            actor.set_actor_rotation(rot,False)
        changed_center,_=actor.get_actor_bounds(False,True)
        actor.set_actor_location(actor.get_actor_location()+center-changed_center+unreal.Vector(0,-20,0),False,True)
preview_camera = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0,0,170))
preview_camera.set_actor_label('LabB_TransientReviewCamera')
state = {'phase': 'setup', 'deadline': time.monotonic()+180, 'index': 0, 'busy': False}

def save():
    (OUT/'Review.json').write_text(json.dumps(report, indent=2))

def tick(delta):
    if state['busy']: return
    state['busy'] = True
    try:
        now = time.monotonic()
        if state['phase'] == 'exit':
            if now > state['deadline']:
                unreal.unregister_slate_post_tick_callback(handle)
                unreal.SystemLibrary.quit_editor()
            return
        if now > state['deadline']: raise TimeoutError('PIE capture timeout: '+state['phase'])
        game = unreal.EditorLevelLibrary.get_game_world()
        if not game: return
        if state['phase'] == 'setup':
            pc = unreal.GameplayStatics.get_player_controller(game, 0)
            if not pc: return
            unreal.GameplayStatics.set_game_paused(game, False)
            camera = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game, unreal.CameraActor) if a.get_actor_label() == 'LabB_TransientReviewCamera')
            camera.camera_component.set_editor_property('field_of_view', 65.)
            if closeups:
                camera.camera_component.set_editor_property('field_of_view', 85.)
                if not lit_closeups: unreal.SystemLibrary.execute_console_command(game,'viewmode unlit')
                report['frame_collision_in_pie']=[{'label':a.get_actor_label(),'enabled':str(a.get_component_by_class(unreal.StaticMeshComponent).get_collision_enabled()),'profile':str(a.get_component_by_class(unreal.StaticMeshComponent).get_collision_profile_name())}
                    for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.StaticMeshActor) if a.get_actor_label().startswith('WorldExpansion_WallArt_LabB_')]
                report['normal_view_sightlines']=[]
                for p in placements:
                    target=unreal.Vector(*p['bounds_center_cm'])
                    start=unreal.Vector(target.x,850.,target.z)
                    hit=unreal.SystemLibrary.line_trace_single(game,start,target,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
                    values=hit.to_tuple() if hit else None
                    report['normal_view_sightlines'].append({'picture':p['label'],'blocking_actor':values[9].get_actor_label() if values and values[0] and values[9] else None})
            pc.set_view_target_with_blend(camera, 0.)
            if pc.get_hud(): pc.get_hud().set_editor_property('show_hud', False)
            pawn = unreal.GameplayStatics.get_player_pawn(game,0)
            if pawn: pawn.set_actor_hidden_in_game(True)
            state.update(camera=camera, game=game, phase='position')
        if state['phase'] == 'position':
            if state['index'] == len(CASES):
                report['capture_complete'] = True
                save(); le.editor_request_end_play(); state.update(phase='exit',deadline=now+4); return
            name, pos, target = CASES[state['index']]
            camera = state['camera']
            camera.set_actor_location(unreal.Vector(*pos), False, True)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos), unreal.Vector(*target)), False)
            state.update(phase='settle',ready=now+(1 if closeups else 6),deadline=now+90)
        elif state['phase'] == 'settle' and now >= state['ready']:
            name, pos, target = CASES[state['index']]
            path = OUT/(name+'.png')
            unreal.SystemLibrary.execute_console_command(game, 'HighResShot 1280x800 filename="'+path.as_posix()+'"')
            state.update(phase='image',requested=time.time())
        elif state['phase'] == 'image':
            name, pos, target = CASES[state['index']]
            path = OUT/(name+'.png')
            if path.exists() and path.stat().st_mtime >= state['requested']-1 and path.stat().st_size > 10000:
                report['captures'].append({'name':name,'image':str(path),'camera_cm':pos,'target_cm':target})
                save(); state.update(index=state['index']+1,phase='position',deadline=now+90)
    except Exception:
        report['errors'].append(traceback.format_exc()); save()
        le.editor_request_end_play(); state.update(phase='exit',deadline=time.monotonic()+4)
    finally:
        state['busy']=False

save()
handle = unreal.register_slate_post_tick_callback(tick)
le.editor_request_begin_play()
