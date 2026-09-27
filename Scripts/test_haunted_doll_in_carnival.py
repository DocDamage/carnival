"""Play the placed Carnival encounter with the project's real player and terrain."""
import json,time,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\HauntedDollIntegration')
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.editor_request_begin_play()
state={'busy':False,'deadline':time.monotonic()+90,'setup':False,'finishing':False,'states':[]}
report={'map':world.get_path_name(),'success':False}
def finish(error=None):
    report['states']=state['states']
    if error:report['error']=error
    (OUT/'Carnival_Playtest.json').write_text(json.dumps(report,indent=2))
    unreal.log_warning('DOLL_CARNIVAL_PLAYTEST '+json.dumps(report))
    levels.editor_request_end_play()
    state['finishing']=True;state['deadline']=time.monotonic()+2
def tick(delta):
    if state['busy']:return
    state['busy']=True
    try:
        if state['finishing']:
            if time.monotonic()>state['deadline']:
                unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if time.monotonic()>state['deadline']:
            finish('Timed out waiting for the full placed encounter.');return
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:return
        if not state['setup']:
            dolls=[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CarnivalHauntedDoll) if 'Carnival.HauntedDoll.MainEncounter' in [str(t) for t in a.tags]]
            player=unreal.GameplayStatics.get_player_pawn(game,0)
            if not dolls or not player:return
            assert isinstance(player,unreal.CarnivalPlayerCharacter),player.get_class().get_name()
            doll=dolls[0];origin=doll.get_actor_location()
            destination=origin+doll.get_actor_forward_vector()*450
            hit=unreal.SystemLibrary.line_trace_single(game,destination+unreal.Vector(0,0,400),destination-unreal.Vector(0,0,400),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[doll,player],unreal.DrawDebugTrace.NONE,True)
            assert hit and hit.to_tuple()[0]
            destination.z=hit.to_tuple()[5].z+98
            player.set_actor_location(destination,False,True)
            player.set_actor_rotation(unreal.Rotator(pitch=0,yaw=doll.get_actor_rotation().yaw+180,roll=0),True)
            unreal.GameplayStatics.set_global_time_dilation(game,3.0)
            state.update({'setup':True,'doll':doll,'player':player,'start':time.monotonic()})
            report.update({'player_class':player.get_class().get_name(),'doll_start':str(origin),'player_start':str(destination),'can_see_player':doll.can_detect_pawn(player)})
            assert report['can_see_player'],'Placed doll cannot see the real player on the verified approach.'
        doll=state['doll']
        encounter=doll.get_editor_property('encounter_state')
        name=encounter.name
        if not state['states'] or state['states'][-1]['state']!=name:
            state['states'].append({'state':name,'wall_seconds':round(time.monotonic()-state['start'],2),'location':str(doll.get_actor_location())})
        visited={s['state'] for s in state['states']}
        if 'RETURNING' in visited and encounter==unreal.DollEncounterState.IDLE:
            count=doll.get_editor_property('scare_count')
            report['scare_count']=count
            report['success']=count==1 and all(n in visited for n in ['NOTICE','APPROACH','CHASE','SCARE','COOLDOWN','RETURNING'])
            finish(None if report['success'] else 'Encounter missed a required state.')
    except Exception:finish(traceback.format_exc())
    finally:state['busy']=False
handle=unreal.register_slate_post_tick_callback(tick)
