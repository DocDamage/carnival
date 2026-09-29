"""PIE acceptance of every authored staffed attraction in the connected map.

Uses production boarding/operator APIs with the actual player. It measures seat
motion, attachment, return and unload, then staff/player handover. No physical
input is injected. Optional rendered captures use CARNIVAL_RIDE_CAPTURE=1.
Changes to durations, fixtures and crowd spawners are unsaved PIE/test changes.
"""
import json
import os
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT/'Saved/RideDevelopment/AllRidePIE'
OUT.mkdir(parents=True, exist_ok=True)
MAP = '/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
SELECTED = set(filter(None, os.environ.get('CARNIVAL_RIDE_FAMILIES','').split(',')))
CAPTURE = os.environ.get('CARNIVAL_RIDE_CAPTURE') == '1'
AUTHORING_PATH = ROOT/'Saved/RideDevelopment/All_Attended_Authoring.json'
AUTHORED = json.loads(AUTHORING_PATH.read_text()).get('rides', []) if AUTHORING_PATH.exists() else []
LE = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
S = {'phase':'startup','busy':False,'deadline':time.monotonic()+300,'index':0}
REPORT = {'started':time.time(),'map':MAP,'tests':[],'errors':[],
          'physical_input':False,'rendered':CAPTURE,'mass_spawners_excluded':[],
          'coverage':'Authored attendants only; consult Placed_Ride_Inventory for unstaffed attractions'}

def save():
    REPORT['phase']=S['phase']
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))

def check(name, passed, **details):
    row = REPORT['tests'][-1]
    row['checks'].append({'name':name,'passed':bool(passed),**details})
    save()
    return bool(passed)

def finish():
    REPORT['success']=bool(REPORT['tests']) and not REPORT['errors'] and all(
        row['checks'] and all(c['passed'] for c in row['checks']) for row in REPORT['tests'])
    save(); LE.editor_request_end_play()
    S.update(phase='exit',deadline=time.monotonic()+4)

def next_ride():
    S['index']+=1
    S['phase']='begin'
    S['deadline']=time.monotonic()+100
    if S['index']>=len(S['staff']): finish()

def tick(_):
    if S['busy']: return
    S['busy']=True
    try:
        if S['phase']=='exit':
            if time.monotonic()>S['deadline']:
                unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        if time.monotonic()>S['deadline']:
            REPORT['errors'].append('Timeout: '+S['phase']); finish(); return
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game: return
        now=unreal.GameplayStatics.get_time_seconds(game)
        if S['phase']=='startup':
            player=unreal.GameplayStatics.get_player_pawn(game,0)
            if not isinstance(player,unreal.CarnivalPlayerCharacter): return
            staff=list(unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CarnivalRideAttendant))
            if SELECTED: staff=[a for a in staff if str(a.get_editor_property('ride_name')) in SELECTED]
            staff.sort(key=lambda a:a.get_name())
            REPORT['attendant_count']=len(staff)
            if not staff: REPORT['errors'].append('No authored attendants loaded'); finish(); return
            S.update(game=game,player=player,staff=staff,phase='begin')
        player=S['player']
        if S['phase']=='begin':
            staff=S['staff'][S['index']]; ride=staff.get_editor_property('ride')
            operation=staff.get_editor_property('operation')
            row={'attendant':staff.get_name(),'ride':ride.get_name() if ride else None,
                 'family':str(staff.get_editor_property('ride_name')),'checks':[]}
            REPORT['tests'].append(row)
            if not check('Operation ready',operation and operation.is_ready(),
                         error=str(operation.get_editor_property('configuration_error')) if operation else 'missing'):
                next_ride(); return
            row['authored_timing']={key:float(getattr(operation,key)) for key in
                ('boarding_seconds','securing_seconds','cycle_seconds','return_seconds','unloading_seconds')}
            # Reuse the clearance-checked authoring position. Vendor actor pivots
            # need not match their mesh bounds centers used to author the approach.
            authored=next((r for r in AUTHORED if r.get('path','').rsplit('.',1)[-1]==ride.get_name()
                           and r.get('placement',{}).get('approach')), None)
            bounds_origin,_=ride.get_actor_bounds(False)
            outward=staff.get_actor_location()-bounds_origin; outward.z=0
            if outward.length()<1: outward=unreal.Vector(1,0,0)
            entry=(unreal.Vector(*authored['placement']['approach']) if authored else
                   staff.get_actor_location()+outward.normal()*180)+unreal.Vector(0,0,6)
            row['approach_source']='saved_authoring_clearance_check' if authored else 'mesh_bounds_direction_fallback'
            row['requested_entry']=list(entry.to_tuple())
            player.set_actor_location(entry,False,True)
            row['teleport_succeeded']=unreal.Vector.distance(player.get_actor_location(),entry)<1
            player.get_movement_component().stop_movement_immediately()
            S.update(operation=operation,ride=ride,staff_actor=staff,entry=entry,
                     phase='settle',until=now+.2,deadline=time.monotonic()+180)
            return
        operation=S['operation']
        if S['phase']=='settle':
            if now<S['until']: return
            S['entry']=player.get_actor_location()
            attendant=operation.get_editor_property('attendant')
            operator=operation.get_editor_property('player_operator')
            diagnostics={'ready':operation.is_ready(),'state':str(operation.get_editor_property('state')),
                         'experience':str(operation.get_editor_property('experience')),
                         'in_interaction_range':operation.is_in_interaction_range(player),
                         'interaction_distance':operation.get_editor_property('interaction_distance'),
                         'passenger_count':operation.get_passenger_count(),
                         'player_location':list(player.get_actor_location().to_tuple()),
                         'attendant_location':list(attendant.get_actor_location().to_tuple()) if attendant else None,
                         'attendant_matches':attendant==S['staff_actor'],
                         'player_operator':operator.get_path_name() if operator else None,
                         'player_movement_mode':str(player.get_movement_component().get_editor_property('movement_mode')),
                         'player_already_riding':player.get_editor_property('ride_passenger').is_riding()}
            if attendant:
                diagnostics['distance_cm']=unreal.Vector.distance(player.get_actor_location(),attendant.get_actor_location())
            if not check('Visitor interaction accepted',operation.request_board(player),preconditions=diagnostics):
                next_ride(); return
            seat=player.get_editor_property('ride_passenger').get_current_seat()
            standing=bool(seat and seat.get_editor_property('standing_passenger'))
            S.update(seat=seat,home=seat.get_world_transform() if seat else None,max_travel=0.,max_error=0.,
                     phase='running',until=now+1.,capture_done=False,saw_running=False)
            check('Seated or standing boarding matches experience', bool(seat) == (operation.get_editor_property('experience')==unreal.CarnivalRideExperience.SEATED_RIDE))
            REPORT['tests'][-1]['standing_passenger']=standing
            return
        if S['phase']=='running':
            seat=S['seat']
            if seat:
                S['max_travel']=max(S['max_travel'],unreal.Vector.distance(seat.get_world_location(),S['home'].translation))
                S['max_error']=max(S['max_error'],unreal.Vector.distance(player.get_actor_location(),seat.get_passenger_world_transform().translation))
            phase=operation.get_editor_property('state')
            if CAPTURE and not S['capture_done'] and now>S['until']+1:
                path=OUT/(str(S['index'])+'_'+REPORT['tests'][-1]['family']+'.png')
                S['capture_task']=unreal.AutomationLibrary.take_high_res_screenshot(1280,800,str(path))
                REPORT['tests'][-1]['capture']=str(path); S['capture_done']=True
            if phase==unreal.CarnivalOperationState.RUNNING:
                S['saw_running']=True
                REPORT['tests'][-1]['motion_components']=[{
                    'name':c.get_name(),'rate':str(c.rotation_rate),
                    'tick_enabled':c.is_component_tick_enabled(),
                    'updated_component':c.updated_component.get_name() if c.updated_component else None}
                    for c in S['ride'].get_components_by_class(unreal.RotatingMovementComponent)]
            if phase==unreal.CarnivalOperationState.RETURNING and S.get('saw_running'):
                if seat:
                    check('Occupied seat physically moves',S['max_travel']>5,travel_cm=S['max_travel'])
                    check('Passenger stays attached',S['max_error']<5,max_error_cm=S['max_error'])
                    check('Authored cycle reaches automatic return',True)
                else:
                    check('Show/walkthrough leaves visitor free',not player.get_editor_property('ride_passenger').is_riding()
                          and player.get_actor_enable_collision())
                    # Let the authored staff cycle complete without a seated exit.
                S.update(phase='unload')
            return
        if S['phase']=='unload':
            if operation.get_editor_property('state')!=unreal.CarnivalOperationState.LOADING: return
            if S['seat']:
                check('Passenger unloaded',not player.get_editor_property('ride_passenger').is_riding())
                check('Passenger collision restored',player.get_actor_enable_collision())
                error=unreal.Vector.distance(S['seat'].get_world_location(),S['home'].translation)
                check('Seat returned to loading position',error<2,position_error_cm=error)
                error=unreal.Vector.distance(player.get_actor_location(),S['entry'])
                check('Exit restored boarding ground position',error<25,position_error_cm=error)
            if not check('Player takes operator control',operation.take_operator_control(player)):
                next_ride(); return
            check('Operator starts cycle',operation.operator_start(player))
            S.update(phase='operator',until=now+float(operation.securing_seconds)+1)
            return
        if S['phase']=='operator':
            if now<S['until']: return
            check('Operator stop requests return',operation.operator_stop(player))
            operation.release_operator_control(player)
            check('Handover releases player ownership',not operation.get_editor_property('player_operator'))
            S.update(phase='handback')
            return
        if S['phase']=='handback':
            if operation.get_editor_property('state')!=unreal.CarnivalOperationState.LOADING: return
            check('Attendant completes handed-back cycle',operation.get_editor_property('completed_cycles')>=2)
            next_ride()
    except Exception:
        REPORT['errors'].append(traceback.format_exc()); finish()
    finally:
        S['busy']=False

world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if actor.get_class().get_name()=='MetaHumanMassSpawner':
        REPORT['mass_spawners_excluded'].append(actor.get_actor_label()); actors.destroy_actor(actor)
save()
handle=unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
