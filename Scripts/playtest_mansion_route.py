"""Drive the real character and motorcycle along the complete saved route in PIE."""
import sys,time,math,json,traceback
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import *
world=unreal.EditorLoadingAndSavingUtils.load_map(CARNIVAL)
# Route traversal does not require the unrelated crowd's MetaHuman outfit builds.
# Remove its spawner only in this unsaved test world to keep the test bounded.
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
excluded=[]
for actor in list(eas.get_all_level_actors()):
    if actor.get_class().get_name()=='MetaHumanMassSpawner':
        excluded.append(actor.get_actor_label());eas.destroy_actor(actor)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.editor_request_begin_play()
route=[unreal.Vector(*p) for p in route_manifest()['route_world']]
report={'success':False,'map':CARNIVAL,'tests':[],'excluded_unrelated_crowd_spawners':excluded}
(OUT/'Route_Playtest.json').write_text(json.dumps(report,indent=2))
(OUT/'Route_Playtest_Live.json').write_text(json.dumps({'mode':'setup'}))
state={'phase':'setup','busy':False,'deadline':time.monotonic()+90,'index':1,'last_index':0,'last_progress':0,'ticks':0}
def xy(a,b):return math.hypot(a.x-b.x,a.y-b.y)
def clock(game):return unreal.GameplayStatics.get_time_seconds(game)
def finish(error=None):
    if error:report['error']=error
    report['last_index']=state['index'];report['phase']=state['phase']
    (OUT/'Route_Playtest.json').write_text(json.dumps(report,indent=2))
    levels.editor_request_end_play();state.update(phase='exit',deadline=time.monotonic()+2)
def begin_mode(mode,game,player,bike=None):
    p=route[0];actor=player if mode=='walk' else bike
    q=route[1];yaw=math.degrees(math.atan2(q.y-p.y,q.x-p.x))
    player.get_movement_component().stop_movement_immediately()
    if mode=='walk':
        actor.set_actor_location(p+unreal.Vector(0,0,100),False,True)
    else:
        bike.input_throttle(0);bike.input_brake(1)
        actor.set_actor_location(p+unreal.Vector(0,0,4),False,True)
        player.set_actor_location(p+unreal.Vector(0,100,102),False,True)
        bike.mount(player,True)
        bike.input_brake(0)
    actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),True)
    now=clock(game)
    state.update(phase=mode,index=1,last_index=0,start=now,last_progress=now,deadline=time.monotonic()+160,actor=actor)
    report['tests'].append({'mode':mode,'start':list(actor.get_actor_location().to_tuple()),'max_abs_pitch':0,'samples':[]})
    unreal.GameplayStatics.set_global_time_dilation(game,4.0)
def tick(delta):
    if state['busy']:return
    state['busy']=True
    try:
        if state['phase']=='exit':
            if time.monotonic()>state['deadline']:
                unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if time.monotonic()>state['deadline']:finish('Timed out in '+state['phase']);return
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:return
        if state['phase']=='setup':
            player=unreal.GameplayStatics.get_player_pawn(game,0)
            bikes=list(unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CarnivalMotorcycle))
            if not player or not bikes:return
            assert isinstance(player,unreal.CarnivalPlayerCharacter),player.get_class().get_name()
            state.update(game=game,player=player,bike=bikes[0])
            report['player_class']=player.get_class().get_name();report['motorcycle_class']=bikes[0].get_class().get_name()
            begin_mode('walk',game,player);return
        actor=state['actor'];pos=actor.get_actor_location();now=clock(game)
        # Nearest forward sample avoids circling a waypoint after a long engine frame.
        nearest=min(range(max(0,state['index']-2),min(len(route),state['index']+18)),key=lambda i:xy(pos,route[i]))
        state['index']=max(state['index'],nearest)
        while state['index']<len(route)-1 and xy(pos,route[state['index']])<100:state['index']+=1
        if state['index']>state['last_index']:
            state.update(last_index=state['index'],last_progress=now)
        if now-state['last_progress']>12:
            report['stuck_location']=list(pos.to_tuple());finish('No progress for 12 game seconds');return
        current=report['tests'][-1]
        current['max_abs_pitch']=max(current['max_abs_pitch'],abs(actor.get_actor_rotation().pitch))
        if pos.z<route[state['index']].z-180:
            report['fall_location']=list(pos.to_tuple());finish('Actor fell below the route');return
        state['ticks']+=1
        if state['ticks']%60==0:
            current['samples'].append({'i':state['index'],'position':list(pos.to_tuple()),'seconds':round(now-state['start'],2)})
            (OUT/'Route_Playtest_Live.json').write_text(json.dumps({'mode':state['phase'],'index':state['index'],'total':len(route),'seconds':now-state['start'],'position':list(pos.to_tuple())}))
        if state['index']==len(route)-1 and xy(pos,route[-1])<125:
            current.update(success=True,seconds=round(now-state['start'],2),finish=list(pos.to_tuple()))
            if state['phase']=='walk':
                begin_mode('motorcycle',game,state['player'],state['bike']);return
            actor.input_throttle(0);actor.input_brake(1)
            report['success']=True;finish();return
        target_index=state['index']
        lookahead=170 if state['phase']=='walk' else 620
        while target_index<len(route)-1 and xy(pos,route[target_index])<lookahead:target_index+=1
        target=route[target_index];direction=unreal.Vector(target.x-pos.x,target.y-pos.y,0)
        length=math.hypot(direction.x,direction.y)
        direction=direction/max(length,1)
        desired=math.degrees(math.atan2(direction.y,direction.x))
        if state['phase']=='walk':actor.add_movement_input(direction,1.0,True)
        else:
            yaw=actor.get_actor_rotation().yaw;error=(desired-yaw+180)%360-180
            actor.input_steering(max(-1,min(1,error/13)))
            actor.input_throttle(.29 if abs(error)<15 else .18)
    except Exception:finish(traceback.format_exc())
    finally:state['busy']=False
handle=unreal.register_slate_post_tick_callback(tick)
