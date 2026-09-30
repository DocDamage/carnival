"""Read-only census of constructed placed ride seats and readiness in PIE."""
import collections
import json
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/RideDevelopment/ConstructedSeatIds.json'
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT={'success':False,'rides':[],'errors':[],'maps_saved':False,'physical_input':False}
S={'phase':'setup','deadline':time.monotonic()+180,'busy':False}

def tick(_):
    if S['busy']: return
    S['busy']=True
    try:
        now=time.monotonic()
        if S['phase']=='exit':
            if now>S['deadline']: unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:
            if now>S['deadline']: raise RuntimeError('PIE startup timeout')
            return
        if S['phase']=='setup': S.update(phase='settle',ready=now+2); return
        if now<S['ready']: return
        for staff in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CarnivalRideAttendant):
            ride=staff.ride
            if not ride: continue
            seats=[]
            for seat in ride.get_components_by_class(unreal.CarnivalRideSeatComponent):
                parent=seat.get_attach_parent()
                seats.append({'component':seat.get_name(),'seat_id':str(seat.seat_id),
                    'parent':parent.get_name() if parent else None,
                    'location':list(seat.get_world_location().to_tuple()),'path':seat.get_path_name()})
            counts=collections.Counter(row['seat_id'] for row in seats)
            REPORT['rides'].append({'ride':ride.get_path_name(),'class':ride.get_class().get_path_name(),
                'family':str(staff.ride_name),'ready':bool(staff.operation and staff.operation.is_ready()),
                'configuration_error':str(staff.operation.configuration_error) if staff.operation else 'missing operation',
                'seats':seats,'duplicates':{key:count for key,count in counts.items() if count>1}})
        REPORT['success']=bool(REPORT['rides']) and all(
            ride['ready'] and not ride['duplicates'] and all(
                seat['seat_id'] not in ('','None') for seat in ride['seats'])
            for ride in REPORT['rides'])
        REPORT['unready_rides']=[{'ride':ride['ride'],'configuration_error':ride['configuration_error']}
                                for ride in REPORT['rides'] if not ride['ready']]
        OUT.write_text(json.dumps(REPORT,indent=2)); LE.editor_request_end_play(); S.update(phase='exit',deadline=now+3)
    except Exception:
        REPORT['errors'].append(traceback.format_exc()); OUT.write_text(json.dumps(REPORT,indent=2))
        LE.editor_request_end_play(); S.update(phase='exit',deadline=time.monotonic()+3)
    finally: S['busy']=False

assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if actor.get_class().get_name()=='MetaHumanMassSpawner': actors.destroy_actor(actor)
handle=unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
