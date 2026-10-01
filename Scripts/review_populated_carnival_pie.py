"""Inspect actual live Mass representations with crowd enabled; never save maps.

Run in render-pie mode. Captures and editor frame samples require separate visual
review and do not establish packaged performance or physical controller input.
"""
import collections
import json
import math
import os
import re
import struct
import time
import traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/PresentationAcceptance'/os.environ.get('CARNIVAL_POPULATED_REPORT','PopulatedCarnival')
OUT.mkdir(parents=True,exist_ok=True)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT={'success':False,'spawners':[],'live_components':[],'captures':[],
        'errors':[],'assets_modified':False,'spawners_removed':False,
        'visual_review':'pending','performance_acceptance':False,'physical_input':False,
        'limits':'Live component instance counts include body/clothing parts, not unique people. Camera captures inspect real spawned representations. Frame intervals are editor/PIE wall time, not packaged game/GPU benchmarks.'}
S={'phase':'setup','deadline':time.monotonic()+1200,'busy':False,'intervals':[]}

def save():
    REPORT['phase']=S['phase']
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))

def finish(error=None):
    if error: REPORT['errors'].append(error)
    intervals=sorted(S['intervals'])
    if intervals:
        REPORT['editor_frame_interval_ms']={'samples':len(intervals),
            'median':intervals[len(intervals)//2],
            'p95':intervals[min(len(intervals)-1,int(len(intervals)*.95))],
            'max':intervals[-1]}
    REPORT['success']=not REPORT['errors'] and len(REPORT['captures'])>=2 and bool(REPORT['live_components'])
    save(); LE.editor_request_end_play(); S.update(phase='exit',deadline=time.monotonic()+4)

def census(game):
    targets={}
    groups=set()
    rows=[]
    actors=list(unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor))
    REPORT['activity_presentation']=[{'actor':a.get_path_name(),
        'authored_name':a.get_editor_property('activity_name'),'display_title':a.get_display_title(),
        'description':a.get_editor_property('description'),
        'world_text':str(a.get_editor_property('prompt_text').get_editor_property('text')),
        'world_size':a.get_editor_property('prompt_text').get_editor_property('world_size'),
        'hidden_in_game':a.get_editor_property('prompt_text').get_editor_property('hidden_in_game')}
        for a in actors if isinstance(a,unreal.CarnivalActivityBase)]
    assert all(not row['world_text'].startswith('Activity_') and '\n' not in row['world_text']
               and row['world_size']==14 for row in REPORT['activity_presentation'])
    REPORT['skylights']=[{'actor':a.get_path_name(),
        'lower_hemisphere_color':list(a.get_component_by_class(unreal.SkyLightComponent).get_editor_property('lower_hemisphere_color').to_tuple()),
        'intensity':a.get_component_by_class(unreal.SkyLightComponent).get_editor_property('intensity')}
        for a in actors if isinstance(a,unreal.SkyLight)]
    REPORT['actor_class_counts']=dict(collections.Counter(a.get_class().get_path_name() for a in actors))
    REPORT['simulation_state']={'paused':unreal.GameplayStatics.is_game_paused(game),
        'game_seconds':unreal.GameplayStatics.get_time_seconds(game),
        'global_time_dilation':unreal.GameplayStatics.get_global_time_dilation(game)}
    pawn=unreal.GameplayStatics.get_player_pawn(game,0)
    REPORT['simulation_state']['player_location_cm']=pawn.get_actor_location().to_tuple() if pawn else None
    REPORT['mass_simulation_diagnostics']=list(unreal.CarnivalCrowdEditorLibrary.describe_live_mass_simulation(game))
    REPORT['skeletal_actor_components']=[]
    for actor in actors:
        for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh=component.get_editor_property('skeletal_mesh_asset')
            if not mesh:continue
            REPORT['skeletal_actor_components'].append({'actor':actor.get_path_name(),
                'class':actor.get_class().get_path_name(),'component':component.get_name(),
                'mesh':mesh.get_path_name(),'location':component.get_world_location().to_tuple(),
                'visible':component.is_visible(),'hidden_actor':actor.get_editor_property('hidden')})
    for actor in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor):
        for component in actor.get_components_by_class(unreal.InstancedSkinnedMeshComponent):
            count=component.get_instance_count()
            if not count: continue
            mesh=component.get_skinned_asset()
            path=mesh.get_path_name() if mesh else None
            row={'component':component.get_path_name(),'mesh':path,'instance_count':count,
                 'materials':[component.get_material(i).get_path_name() if component.get_material(i) else None
                              for i in range(component.get_num_materials())]}
            rows.append(row)
            match=re.search(r'DA_CarnivalCrowd_G([1-6])_FINAL2',path or '')
            if match:
                group=match.group(1)
                groups.add(group)
                # Prefer body components over a clothing/groom part when present.
                score=int('body' in (component.get_name()+' '+path).lower())
                if group not in targets or score>targets[group]['score']:
                    transform=component.get_instance_transform(component.get_instance_id(0),True)
                    if transform:
                        targets[group]={'name':'CrowdGroup_'+group,'point':transform.translation,'score':score,'source':row}
    REPORT['live_components']=rows
    REPORT['live_collection_groups']=sorted(groups)
    # GPU-only skinned instance data has a count but no CPU-readable transform.
    # Use real Mass transforms for lane viewpoints instead of treating an invalid
    # GPU instance ID as absence of a rendered crowd.
    lane_targets={}
    for entity in unreal.CarnivalCrowdEditorLibrary.sample_live_crowd_entities(game):
        if entity.lane_index < 0 or entity.lane_index in lane_targets: continue
        lane_targets[entity.lane_index]={'name':f'CrowdLane_{entity.lane_index}', 'point':entity.location,
            'entity_id':[entity.entity_index,entity.entity_serial],
            'source':{'kind':'mass_entity','lane_at_selection':entity.lane_index,
                      'limits':'Actual entity position for a lane viewpoint; collection/individual appearance acceptance is separate.'}}
    return [targets[k] for k in sorted(targets)]+[lane_targets[k] for k in sorted(lane_targets)]

def tick(_):
    if S['busy']: return
    S['busy']=True
    try:
        now=time.monotonic()
        if S['phase']=='exit':
            if now>S['deadline']:
                unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        game=unreal.EditorLevelLibrary.get_game_world()
        if now>S['deadline']:
            if game and S['phase']=='warm':
                REPORT['timeout_census']=True
                census(game)
            finish('Timeout in '+S['phase']); return
        if not game: return
        if S['phase']=='setup':
            pc=unreal.GameplayStatics.get_player_controller(game,0)
            if not pc: return
            spawners=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.MassSpawner)
            REPORT['spawners']=[{'actor':a.get_path_name(),'configured_count':a.get_count(),
                                'count_scale':a.get_spawning_count_scale(),
                                'auto_spawn_on_begin_play':a.get_editor_property('auto_spawn_on_begin_play'),
                                'override_schematics':a.get_editor_property('override_schematics'),
                                'entity_types':str(a.get_editor_property('entity_types')),
                                'spawn_data_generators':str(a.get_editor_property('spawn_data_generators'))} for a in spawners]
            if not spawners: finish('No active Mass spawner'); return
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
            REPORT['asset_streaming_wait_started']=True;save()
            for spawner in spawners:
                spawner.wait_for_streaming_assets()
            REPORT['asset_streaming_wait_complete']=True
            now=time.monotonic()
            REPORT['warmup_limits']={'wall_seconds_minimum':30,'game_seconds_minimum':20,
                'cold_asset_compilation_timeout_seconds':1200,
                'limits':'Cold editor compilation allowance; not a frame-rate/performance acceptance.'}
            S.update(phase='warm',pc=pc,game=game,ready=now+30,last_frame=now,
                     game_start=unreal.GameplayStatics.get_time_seconds(game),deadline=now+1200,
                     arrival_view=pc.get_view_target())
            save(); return
        if S['phase']=='warm':
            S['intervals'].append((now-S['last_frame'])*1000); S['last_frame']=now
            if now<S['ready']: return
            if unreal.GameplayStatics.get_time_seconds(game)-S['game_start']<20: return
            targets=census(game)
            if not REPORT['live_components']:
                diagnostics=REPORT['mass_simulation_diagnostics']
                sample=next((re.search(r'^CrowdSample Location=X=([-\d.]+) Y=([-\d.]+) Z=([-\d.]+)',line)
                             for line in diagnostics if line.startswith('CrowdSample Location=')),None)
                count=next((int(line.split('=')[1]) for line in diagnostics if line.startswith('CrowdEntitiesWithTransforms=')),0)
                if not count or not sample:
                    finish('No live representation or actual crowd transform available'); return
                point=unreal.Vector(*(float(value) for value in sample.groups()))
                assert all(math.isfinite(value) for value in point.to_tuple())
                REPORT['arrival_mass_diagnostics']=list(diagnostics)
                REPORT['crowd_focus_reason']='Actual entities exist outside arrival viewer range. Move only transient review camera to a sampled live transform; no entity/player/spawner/LOD changes.'
                targets=[{'name':'CrowdLaneApproach','point':point,'seek_crowd':True}]
            S.update(targets=[{'name':'PlayerArrival','point':None}]+targets+[
                {'name':'ActivityApproach','point':None,'walk_to_activity':True}],index=0,phase='camera',deadline=now+240)
            save(); return
        target=S['targets'][S['index']]
        if S['phase']=='seek_crowd':
            if now<S['ready'] or unreal.GameplayStatics.get_time_seconds(game)-S['seek_game_start']<5: return
            targets=census(game)
            if not REPORT['live_components']:
                finish('No live instanced skin representation near sampled crowd after viewpoint warmup'); return
            S['targets']=S['targets'][:S['index']+1]+targets+[
                {'name':'ActivityApproach','point':None,'walk_to_activity':True}]
            S.update(phase='settle',ready=now+3,deadline=now+240)
            save(); return
        if S['phase']=='camera':
            if target.get('walk_to_activity'):
                player=unreal.GameplayStatics.get_player_character(game,0)
                assert isinstance(player,unreal.CarnivalPlayerCharacter)
                activity=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CarnivalActivityBase)
                              if a.get_editor_property('activity_name')=='Activity_MidwayStuntRally')
                S['pc'].set_view_target_with_blend(S['arrival_view'],0)
                REPORT['activity_approach']={'movement_method':'ordinary Character.AddMovementInput; no teleport, collision bypass or speed override',
                    'physical_input':False,'samples':[],'activity':activity.get_path_name(),
                    'start_position_cm':list(player.get_actor_location().to_tuple())}
                S.update(phase='activity_walk',player=player,activity=activity,
                         walk_start=unreal.GameplayStatics.get_time_seconds(game),last_sample=-1,deadline=now+240)
                save(); return
            if target.get('entity_id'):
                entity=next((e for e in unreal.CarnivalCrowdEditorLibrary.sample_live_crowd_entities(game)
                    if [e.entity_index,e.entity_serial]==target['entity_id']),None)
                assert entity is not None, 'Selected crowd entity disappeared before camera setup'
                target['point']=entity.location
            if target['point'] is not None:
                if not S.get('camera'):
                    cameras=[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CameraActor)
                             if a.get_actor_label()=='PopulatedCarnivalReviewCamera']
                    if len(cameras)!=1: raise RuntimeError('Expected one transient review camera in PIE')
                    S['camera']=cameras[0]
                point=target['point']; focus=point+unreal.Vector(0,0,95)
                for index in range(16):
                    angle=index*math.tau/16
                    location=point+unreal.Vector(math.cos(angle)*450,math.sin(angle)*450,160)
                    hit=unreal.SystemLibrary.line_trace_single(game,location,focus,unreal.TraceTypeQuery.ECC_CAMERA,
                        False,[S['camera']],unreal.DrawDebugTrace.NONE,True)
                    if not hit or not hit.to_tuple()[0]: break
                target['camera_ray_clear']=not hit or not hit.to_tuple()[0]
                S['camera'].set_actor_location(location,False,True)
                S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location,focus),True)
                S['pc'].set_view_target_with_blend(S['camera'],0)
                if target.get('seek_crowd'):
                    S.update(phase='seek_crowd',ready=now+10,deadline=now+1200,
                             seek_game_start=unreal.GameplayStatics.get_time_seconds(game))
                    save(); return
            S.update(phase='settle',ready=now+3); return
        if S['phase']=='activity_walk':
            gt=unreal.GameplayStatics.get_time_seconds(game)
            player=S['player']; activity=S['activity']; pos=player.get_actor_location()
            if gt-S['last_sample']>=1:
                REPORT['activity_approach']['samples'].append({'game_seconds':gt,'position_cm':list(pos.to_tuple())})
                S['last_sample']=gt; save()
            if player.get_editor_property('nearby_activity')==activity:
                assert player.find_nearby_mission_interaction() is None, 'Story interaction takes priority over activity prompt at this point'
                REPORT['activity_approach']['trigger_entered']=True
                REPORT['activity_approach']['display_title']=activity.get_display_title()
                REPORT['activity_approach']['end_position_cm']=list(pos.to_tuple())
                REPORT['activity_approach']['walk_seconds']=gt-S['walk_start']
                S.update(phase='settle',ready=now+3); save(); return
            if gt-S['walk_start']>45:
                finish('Ordinary player walk did not enter Midway Stunt Rally trigger within 45 game seconds'); return
            delta=activity.get_actor_location()-pos
            direction=unreal.Vector(delta.x,delta.y,0)/max(1,math.hypot(delta.x,delta.y))
            player.add_movement_input(direction,1.0,True)
            return
        if S['phase']=='settle':
            if now<S['ready']: return
            path=OUT/(target['name']+'.png')
            unreal.SystemLibrary.execute_console_command(game,f'HighResShot 1280x800 filename="{path.as_posix()}"')
            S.update(phase='capture',path=path,requested=time.time()); return
        if S['phase']=='capture':
            path=S['path']
            if not path.exists() or path.stat().st_mtime<S['requested']-1: return
            blob=path.read_bytes()
            if blob[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',blob[16:24])!=(1280,800):
                finish('Unexpected capture dimensions/format'); return
            REPORT['captures'].append({'name':target['name'],'path':str(path),
                'target_cm':list(target['point'].to_tuple()) if target['point'] else None,
                'camera_ray_clear':target.get('camera_ray_clear'),
                'source':target.get('source')})
            S['index']+=1; save()
            if S['index']>=len(S['targets']): finish()
            else: S['phase']='camera'
    except Exception:
        finish(traceback.format_exc())
    finally:
        S['busy']=False

save()
entry=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in ('Editor.AsyncAssetCompilationMaxConcurrency 1',
                'Editor.AsyncStaticMeshCompilationMaxConcurrency 1',
                'Editor.AsyncSkinnedAssetCompilationMaxConcurrency 1',
                'Editor.AsyncTextureCompilationMaxConcurrency 1',
                'Editor.AsyncAssetCompilationMaxMemoryUsage 4'):
    unreal.SystemLibrary.execute_console_command(entry,command)
REPORT['process_local_compilation_limits']={'asset_workers':1,'memory_budget_gib':4,
    'limits':'Compilation-only throttle; scene/crowd/assets and PIE visual wait mode unchanged.'}
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
camera=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector())
camera.set_actor_label('PopulatedCarnivalReviewCamera')
handle=unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
