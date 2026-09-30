"""Walk every saved balloon station route outbound and back with the real pawn.

Initial placement is at the surveyed public access seed. All subsequent movement
uses production walking/collision; there is no intermediate teleport or flight.
Run after author_balloon_stations.py succeeds. Render/physical input acceptance
remain separate from this character movement test.
"""
import json
import hashlib
import math
import os
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/RideDevelopment'
REPORT_NAME=os.environ.get('CARNIVAL_BALLOON_WALK_REPORT','Balloon_Station_Walks')
if not REPORT_NAME.replace('_','').isalnum(): raise ValueError('Unsafe walking report name')
AUTHORING=json.loads((OUT/'Balloon_Stations.json').read_text())
assert AUTHORING.get('success'), 'Ground stations must be authored before player acceptance'
STATIONS=AUTHORING['stations']
assert len(STATIONS)==10, 'Expected all ten station routes'
for index,station in enumerate(STATIONS): station['station_index']=index
selected=os.environ.get('CARNIVAL_BALLOON_STATIONS','')
if selected:
    indices=[int(value) for value in selected.split(',')]
    assert len(set(indices))==len(indices) and all(0<=index<10 for index in indices)
    STATIONS=[STATIONS[index] for index in indices]
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT={'success':False,'physical_input':False,'rendered_acceptance':'pending',
        'movement':'Production CarnivalPlayerCharacter walking input, outbound and return',
        'selected_station_indices':[station['station_index'] for station in STATIONS],
        'tests':[],'errors':[],'excluded_mass_spawners':[]}
REPORT['balloon_stations_sha256']=hashlib.sha256((OUT/'Balloon_Stations.json').read_bytes()).hexdigest()
S={'phase':'startup','deadline':time.monotonic()+300,'busy':False,'case':0}

def save():
    REPORT['phase']=S['phase']
    (OUT/(REPORT_NAME+'.json')).write_text(json.dumps(REPORT,indent=2))

def planar(a,b): return math.hypot(a.x-b.x,a.y-b.y)

def start_leg(reverse=False):
    points=list(STATIONS[S['case']]['walk_route_foot_cm'])
    if reverse: points.reverse()
    assert len(points)>1
    player=S['player']; move=player.get_movement_component()
    move.stop_movement_immediately()
    if not reverse:
        start=unreal.Vector(*points[0])+unreal.Vector(0,0,S['half_height']+5)
        player.set_actor_location(start,False,True)
        if unreal.Vector.distance(player.get_actor_location(),start)>1: raise RuntimeError('Access seed placement failed')
    S.update(phase='settle',reverse=reverse,route=[unreal.Vector(*p) for p in points],waypoint=1,
             until=unreal.GameplayStatics.get_time_seconds(S['world'])+.5,
             deadline=time.monotonic()+180,last_progress=time.monotonic(),last_sample=0.)
    REPORT['tests'].append({'station':STATIONS[S['case']]['station_index'],'ride':STATIONS[S['case']]['ride'],
        'leg':'return' if reverse else 'outbound','success':False,'samples':[],
        'length_m':sum(math.dist(a,b) for a,b in zip(points,points[1:]))/100})
    save()

def finish():
    REPORT['success']=len(REPORT['tests'])==2*len(STATIONS) and not REPORT['errors'] and all(t['success'] for t in REPORT['tests'])
    save(); LE.editor_request_end_play(); S.update(phase='exit',deadline=time.monotonic()+3)

def fail(message):
    REPORT['errors'].append(message)
    if REPORT['tests']: REPORT['tests'][-1]['error']=message
    if S.get('player') and S.get('route'):
        pos=S['player'].get_actor_location(); target=S['route'][min(S['waypoint'],len(S['route'])-1)]
        direction=unreal.Vector(target.x-pos.x,target.y-pos.y,0).normal()
        result=unreal.SystemLibrary.capsule_trace_single(S['world'],pos,pos+direction*150,
            S['radius'],S['half_height'],unreal.TraceTypeQuery.ECC_VISIBILITY,False,
            [S['player']],unreal.DrawDebugTrace.NONE,True)
        hit=result.to_tuple() if result else None
        REPORT['tests'][-1]['failure_position_cm']=list(pos.to_tuple())
        if hit and hit[0]:
            REPORT['tests'][-1]['blocker']=hit[9].get_path_name() if hit[9] else 'unknown'
            REPORT['tests'][-1]['blocking_component']=hit[10].get_path_name() if hit[10] else None
    if S['case']+1<len(STATIONS) and S.get('player'):
        S['case']+=1; start_leg(); return
    finish()

def tick(_):
    if S['busy']: return
    S['busy']=True
    try:
        wall=time.monotonic()
        if S['phase']=='exit':
            if wall>S['deadline']:
                unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        if wall>S['deadline']: fail('Timeout in '+S['phase']); return
        world=unreal.EditorLevelLibrary.get_game_world()
        if not world: return
        now=unreal.GameplayStatics.get_time_seconds(world)
        if S['phase']=='startup':
            player=unreal.GameplayStatics.get_player_pawn(world,0)
            if not isinstance(player,unreal.CarnivalPlayerCharacter): return
            capsule=player.get_component_by_class(unreal.CapsuleComponent)
            S.update(world=world,player=player,radius=capsule.get_scaled_capsule_radius(),
                     half_height=capsule.get_scaled_capsule_half_height())
            REPORT['player_class']=player.get_class().get_name()
            REPORT['capsule_cm']=[S['radius'],S['half_height']]
            controller=player.get_controller()
            if controller: controller.set_ignore_move_input(False)
            unreal.GameplayStatics.set_game_paused(world,False)
            unreal.SystemLibrary.execute_console_command(world,'t.IdleWhenNotForeground 0')
            player.get_movement_component().set_movement_mode(unreal.MovementMode.MOVE_WALKING)
            start_leg(); return
        if unreal.GameplayStatics.is_game_paused(world): unreal.GameplayStatics.set_game_paused(world,False)
        if S['phase']=='settle':
            if now<S['until']: return
            S.update(phase='walk',last_progress=wall,started=now)
        player=S['player']; pos=player.get_actor_location(); points=S['route']; current=REPORT['tests'][-1]
        while S['waypoint']<len(points)-1 and planar(pos,points[S['waypoint']])<55:
            S['waypoint']+=1; S['last_progress']=wall
        target=points[S['waypoint']]
        if wall-S['last_progress']>15: fail('No waypoint progress for 15 seconds'); return
        if pos.z<target.z-100: fail('Player fell below surveyed ground'); return
        if wall-S['last_sample']>1:
            camera=unreal.GameplayStatics.get_player_camera_manager(world,0)
            current['samples'].append({'waypoint':S['waypoint'],'position_cm':list(pos.to_tuple()),
                'camera_cm':list(camera.get_camera_location().to_tuple()) if camera else None,
                'movement_mode':str(player.get_movement_component().get_editor_property('movement_mode'))})
            S['last_sample']=wall; save()
        if S['waypoint']==len(points)-1 and planar(pos,target)<45:
            foot_error=pos.z-S['half_height']-target.z
            if abs(foot_error)>40: fail('Route endpoint reached on wrong floor'); return
            if not S['reverse']:
                staff=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.CarnivalRideAttendant)
                    if a.get_name()==STATIONS[S['case']]['attendant'].rsplit('.',1)[-1]),None)
                op=staff.get_editor_property('operation') if staff else None
                current['attendant_in_reach']=bool(op and op.is_in_interaction_range(player))
                if not current['attendant_in_reach']: fail('Ground route does not reach attendant interaction'); return
            current.update(success=True,seconds=now-S['started'],endpoint_foot_error_cm=foot_error)
            if not S['reverse']: start_leg(True)
            elif S['case']+1<len(STATIONS): S['case']+=1; start_leg()
            else: finish()
            return
        direction=unreal.Vector(target.x-pos.x,target.y-pos.y,0).normal()
        player.add_movement_input(direction,1.,True)
    except Exception: fail(traceback.format_exc())
    finally: S['busy']=False

world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if actor.get_class().get_name()=='MetaHumanMassSpawner':
        REPORT['excluded_mass_spawners'].append(actor.get_path_name())
        actors.destroy_actor(actor) # Unsaved test exclusion, same as other focused PIE harnesses.
save()
handle=unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
