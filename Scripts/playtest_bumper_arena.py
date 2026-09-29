"""PIE: staffed bumper driving, stop/unload, walking return and operator handover.

Uses live native properties without editor property notifications during PIE.
This exercises production APIs, not physical controller input.
"""
import json
import time
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/RideDevelopment/BumperArenaPIE'
OUT.mkdir(parents=True,exist_ok=True)
AUTHORING=json.loads((ROOT/'Saved/RideDevelopment/BumperArena_Authoring.json').read_text())
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT={'checks':[],'errors':[],'physical_input':False,'rendered':False}
S={'phase':'startup','deadline':time.monotonic()+180,'busy':False}


def save():
    REPORT['phase']=S['phase']
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))


def check(name,passed,**details):
    REPORT['checks'].append({'name':name,'passed':bool(passed),**details}); save()
    return bool(passed)


def finish():
    REPORT['success']=bool(REPORT['checks']) and not REPORT['errors'] and all(row['passed'] for row in REPORT['checks'])
    save(); LE.editor_request_end_play(); S.update(phase='exit',deadline=time.monotonic()+4)


def boarding_diagnostics(world, player, staff, operation):
    arena=staff.ride.get_component_by_class(unreal.CarnivalBumperArenaComponent)
    capsule=player.get_component_by_class(unreal.CapsuleComponent)
    assert capsule, 'Production player capsule component missing'
    radius=capsule.get_scaled_capsule_radius()
    half_height=capsule.get_scaled_capsule_half_height()
    row={'ready':operation.is_ready(),'state':str(operation.state),
         'in_range':operation.is_in_interaction_range(player),
         'staff_location':list(staff.get_actor_location().to_tuple()),
         'player_location':list(player.get_actor_location().to_tuple()),
         'player_controller':str(player.get_controller()),'using_ride':player.is_using_ride(),
         'parkour':player.is_parkour_traversing(),'player_operator':str(operation.player_operator),
         'capsule_radius':radius,'capsule_half_height':half_height,'cars':[], 'vendor_car_components':[]}
    REPORT['boarding_diagnostics']=row
    save()
    for car in arena.cars:
        if not car:
            row['cars'].append({'valid':False}); continue
        seat=car.driver_seat.get_passenger_world_transform().translation
        hit=unreal.SystemLibrary.capsule_trace_single_by_profile(world,player.get_actor_location(),seat,
            radius,half_height,'Pawn',False,[player,car],unreal.DrawDebugTrace.NONE,True)
        values=hit.to_tuple() if hit else None
        row['cars'].append({'path':car.get_path_name(),'can_board':car.can_board(player),
            'location':list(car.get_actor_location().to_tuple()),'seat':list(seat.to_tuple()),
            'distance_cm':unreal.Vector.distance(car.get_actor_location(),player.get_actor_location()),
            'speed':car.current_speed,'rider':str(car.current_rider),'arena_matches':car.arena==arena,
            'hull_extent':list(car.hull.get_scaled_box_extent().to_tuple()),
            'seat_occupied':str(car.driver_seat.get_occupant()),
            'pawn_profile_sweep':{'blocked':bool(values and values[0]),
                'hit_fields':[str(value) for value in values] if values else []}})
        save()
    for component in staff.ride.get_components_by_class(unreal.StaticMeshComponent):
        if component.get_name().lower().startswith('sm_bumpercar'):
            row['vendor_car_components'].append({'name':component.get_name(),
                'visible':component.is_visible(),'hidden_in_game':component.get_editor_property('hidden_in_game'),
                'collision':str(component.get_collision_enabled()),'transform':str(component.get_world_transform())})
    REPORT['boarding_diagnostics']=row
    save()


def tick(_):
    if S['busy']: return
    S['busy']=True
    try:
        if S['phase']=='exit':
            if time.monotonic()>S['deadline']:
                unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        if time.monotonic()>S['deadline']:
            REPORT['errors'].append('Timeout in '+S['phase']); finish(); return
        world=unreal.EditorLevelLibrary.get_game_world()
        if not world: return
        now=unreal.GameplayStatics.get_time_seconds(world)
        if S['phase']=='startup':
            player=unreal.GameplayStatics.get_player_pawn(world,0)
            if not isinstance(player,unreal.CarnivalPlayerCharacter): return
            staff=next((actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.CarnivalRideAttendant)
                        if str(actor.ride_name)=='BumperCars'),None)
            if not staff or not staff.operation or not staff.operation.is_ready(): return
            operation=staff.operation
            operation.boarding_seconds=.3; operation.securing_seconds=.3; operation.cycle_seconds=30.; operation.unloading_seconds=.3
            approach=unreal.Vector(*AUTHORING['approach'])
            player.set_actor_location(approach,False,True)
            player.get_movement_component().stop_movement_immediately()
            S.update(player=player,player_scale=player.get_actor_scale3d(),staff=staff,operation=operation,approach=approach,phase='settle',until=now+.3)
            return
        player=S['player']; operation=S['operation']
        if S['phase']=='settle':
            if now<S['until']: return
            check('Driving arena ready',operation.experience==unreal.CarnivalRideExperience.DRIVING_ARENA)
            boarding_diagnostics(world,player,S['staff'],operation)
            if not check('Attendant boards player',operation.request_board(player),player_location=list(player.get_actor_location().to_tuple())):
                finish(); return
            car=unreal.GameplayStatics.get_player_pawn(world,0)
            if not check('Controller possesses drivable bumper car',isinstance(car,unreal.CarnivalBumperCar)):
                finish(); return
            arena=car.arena
            check('Passenger scale preserved',unreal.Vector.distance(player.get_actor_scale3d(),S['player_scale'])<.001)
            extent=car.hull.get_scaled_box_extent()
            S.update(car=car,arena=arena,radius=(extent.x**2+extent.y**2)**.5,start=car.get_actor_location(),travel=0.,phase='start',inside=True)
            return
        car=S['car']
        if S['phase']=='start':
            if operation.state!=unreal.CarnivalOperationState.RUNNING: return
            car.input_throttle(1.); car.input_steering(.25)
            S.update(phase='driving',until=now+6.)
            return
        if S['phase']=='driving':
            S['travel']=max(S['travel'],unreal.Vector.distance(car.get_actor_location(),S['start']))
            S['inside']=S['inside'] and S['arena'].contains_car_location(car.get_actor_location(),S['radius'])
            if now<S['until']: return
            check('Player input moves actual car',S['travel']>100.,max_distance_cm=S['travel'])
            check('Car stays inside measured arena',S['inside'])
            check('Passenger stays in driver seat',player.ride_passenger.is_riding())
            car.request_exit()
            check('Exit requests controlled stop',operation.state==unreal.CarnivalOperationState.RETURNING)
            S.update(phase='unloading')
            return
        if S['phase']=='unloading':
            if player.ride_passenger.is_riding(): return
            check('Unloading returns player possession',unreal.GameplayStatics.get_player_pawn(world,0)==player)
            check('Unloading restores player collision',player.get_actor_enable_collision())
            S.update(phase='walk_back',walk_deadline=now+20.)
            return
        if S['phase']=='walk_back':
            delta=S['approach']-player.get_actor_location(); delta.z=0
            if delta.length()>45:
                if now>S['walk_deadline']:
                    check('Player can walk back to boarding bay',False,distance_cm=delta.length()); finish(); return
                player.add_movement_input(delta.normal(),1.,False)
                return
            player.get_movement_component().stop_movement_immediately()
            check('Player can walk back to boarding bay',True)
            if operation.state!=unreal.CarnivalOperationState.LOADING: return
            if not check('Player takes operator controls',operation.take_operator_control(player)):
                finish(); return
            check('Player starts next session',operation.operator_start(player))
            S.update(phase='operator',until=now+1.)
            return
        if S['phase']=='operator':
            if now<S['until']: return
            check('Operator stops session',operation.operator_stop(player))
            operation.release_operator_control(player)
            S.update(phase='handover')
            return
        if S['phase']=='handover':
            if operation.state!=unreal.CarnivalOperationState.LOADING: return
            check('Attendant regains controls',not operation.player_operator and operation.completed_cycles>=2)
            finish()
    except Exception:
        REPORT['errors'].append(traceback.format_exc()); finish()
    finally:
        S['busy']=False


world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if actor.get_class().get_name()=='MetaHumanMassSpawner': actors.destroy_actor(actor)
save()
handle=unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
