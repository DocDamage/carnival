"""Render transient night-fill comparisons with all 240 live guests; never save assets."""
import json, math, os, struct, sys, time, traceback
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()).resolve()
sys.path.insert(0,str(ROOT/'Scripts'))
from crowd_lighting_survey import survey
OUT=ROOT/'Saved/PresentationAcceptance'/os.environ.get('CARNIVAL_NIGHT_FILL_REPORT','NightFillComparison_20260930')
OUT.mkdir(parents=True,exist_ok=True)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT={'success':False,'errors':[],'captures':[],'variants':[], 'assets_modified':False,
        'density_changed':False,'player_or_entities_teleported':False,'visual_review':'pending',
        'performance_acceptance':False,
        'limits':'Transient PIE skylight comparisons at ordinary arrival and a real guest viewpoint. Separate visual review and saved-content verification are required; no world collision, packaged performance or physical controller acceptance.'}
VARIANTS=[('Baseline',None,None),
          ('LowerBounceSoft',(0.04,0.06,0.09),None),
          ('LowerBounceModerate',(0.12,0.16,0.22),None),
          ('DefaultCubeSoft',None,0.25),
          ('DefaultCubeModerate',None,0.75)]
S={'phase':'setup','busy':False,'deadline':time.monotonic()+1200}

def save():
    REPORT['phase']=S['phase']
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))

def finish(error=None):
    if error: REPORT['errors'].append(error)
    REPORT['success']=not REPORT['errors'] and len(REPORT['captures'])==len(VARIANTS)*2
    save(); LE.editor_request_end_play(); S.update(phase='exit',deadline=time.monotonic()+4)

def skylight_state(component):
    return {'source_type':str(component.get_editor_property('source_type')),
        'intensity':component.get_editor_property('intensity'),
        'light_color':list(component.get_editor_property('light_color').to_tuple()),
        'lower_hemisphere_color':list(component.get_editor_property('lower_hemisphere_color').to_tuple()),
        'lower_hemisphere_is_black':component.get_editor_property('lower_hemisphere_is_black'),
        'affects_world':component.get_editor_property('affects_world'),
        'cubemap':component.get_editor_property('cubemap').get_path_name() if component.get_editor_property('cubemap') else None}

def apply_variant(game):
    name,lower,intensity=VARIANTS[S['variant']]
    component=S['sky']; original=S['original']
    component.set_editor_property('source_type',original['source_type'])
    component.set_editor_property('lower_hemisphere_is_black',original['lower_hemisphere_is_black'])
    component.set_cubemap(original['cubemap'])
    component.set_intensity(original['intensity'])
    component.set_light_color(unreal.MathLibrary.conv_color_to_linear_color(original['light_color']))
    component.set_lower_hemisphere_color(original['lower_hemisphere_color'])
    if lower:
        component.set_editor_property('lower_hemisphere_is_black',True)
        component.set_lower_hemisphere_color(unreal.LinearColor(*lower,1.0))
    if intensity is not None:
        component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
        component.set_cubemap(S['cube'])
        component.set_intensity(intensity)
        component.set_light_color(unreal.LinearColor(0.55,0.65,0.9,1.0))
        component.set_editor_property('lower_hemisphere_is_black',False)
    component.recapture_sky()
    REPORT['variants'].append({'name':name,'settings':skylight_state(component)})
    S.update(phase='variant_warm',ready=time.monotonic()+5,game_ready=unreal.GameplayStatics.get_time_seconds(game)+5,view=0)
    save()

def near_view(game):
    entities=unreal.CarnivalCrowdEditorLibrary.sample_live_crowd_entities(game)
    assert len(entities)==240
    ignore=[S['camera']]
    ignore += [a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
               if a.get_class().get_path_name() in (
                   '/Game/Carnival/Crowd/Actors/BP_CarnivalCrowdActor.BP_CarnivalCrowdActor_C',
                   '/MetaHumanCrowd/BP_CrowdActor.BP_CrowdActor_C')]
    candidates=entities
    if S.get('entity_id'):
        tracked=[e for e in entities if [e.entity_index,e.entity_serial]==S['entity_id']]
        candidates=tracked+[e for e in entities if e not in tracked]
    for entity in candidates[:24]:
        point=entity.location; focus=point+unreal.Vector(0,0,105)
        angle0=math.atan2(entity.velocity.y,entity.velocity.x)
        for i in range(16):
            angle=angle0+i*math.tau/16
            location=point+unreal.Vector(math.cos(angle)*350,math.sin(angle)*350,170)
            hit=unreal.SystemLibrary.line_trace_single(game,location,focus,unreal.TraceTypeQuery.ECC_CAMERA,
                False,ignore,unreal.DrawDebugTrace.NONE,True)
            if hit and hit.to_tuple()[0]: continue
            S['camera'].set_actor_location(location,False,True)
            S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location,focus),True)
            S['pc'].set_view_target_with_blend(S['camera'],0)
            S['entity_id']=[entity.entity_index,entity.entity_serial]
            return {'entity_id':S['entity_id'],'point_cm':list(point.to_tuple()),
                    'camera_cm':list(location.to_tuple()),'world_camera_ray_clear':True,
                    'limits':'Camera ray excludes crowd actors; it verifies world geometry clearance, not crowd body separation.'}
    raise RuntimeError('No clear world-geometry ray for any candidate guest viewpoint')

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
        if now>S['deadline']: finish('Timeout in '+S['phase']); return
        if not game: return
        gt=unreal.GameplayStatics.get_time_seconds(game)
        if S['phase']=='setup':
            pc=unreal.GameplayStatics.get_player_controller(game,0)
            if not pc: return
            spawners=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.MassSpawner)
            REPORT['spawners']=[{'count':a.get_count(),'scale':a.get_spawning_count_scale()} for a in spawners]
            assert sum(a.get_count()*a.get_spawning_count_scale() for a in spawners)==240
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
            REPORT['lighting_before']=survey(game)
            REPORT['world_text_labels']=[{'actor':a.get_path_name(),'label':a.get_actor_label(),
                'component':c.get_path_name(),'text':str(c.get_editor_property('text')),
                'world_size':c.get_editor_property('world_size'),'location_cm':list(c.get_world_location().to_tuple())}
                for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
                for c in a.get_components_by_class(unreal.TextRenderComponent)]
            for spawner in spawners: spawner.wait_for_streaming_assets()
            lights=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.SkyLight)
            assert len(lights)==1
            component=lights[0].get_component_by_class(unreal.SkyLightComponent)
            cameras=[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CameraActor)
                     if a.get_actor_label()=='NightFillComparisonCamera']
            assert len(cameras)==1
            cube=unreal.load_asset('/Engine/EngineMaterials/DefaultCubemap'); assert isinstance(cube,unreal.TextureCube)
            S.update(pc=pc,arrival=pc.get_view_target(),camera=cameras[0],sky=component,cube=cube,
                original={key:component.get_editor_property(key) for key in ('source_type','intensity','light_color',
                    'lower_hemisphere_color','lower_hemisphere_is_black','cubemap')},
                phase='warm',ready=time.monotonic()+30,game_ready=unreal.GameplayStatics.get_time_seconds(game)+20,
                deadline=time.monotonic()+1200,variant=0)
            REPORT['renderer_console_values']={name:unreal.SystemLibrary.get_console_variable_int_value(name)
                for name in ('r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.SupportSkyLight','r.RayTracing',
                             'sg.GlobalIlluminationQuality','sg.ShadowQuality')}
            save(); return
        if unreal.GameplayStatics.is_game_paused(game) or unreal.GameplayStatics.get_global_time_dilation(game)!=1:
            finish('Simulation paused or time dilation changed'); return
        if S['phase']=='warm':
            if now<S['ready'] or gt<S['game_ready']: return
            assert len(unreal.CarnivalCrowdEditorLibrary.sample_live_crowd_entities(game))==240
            apply_variant(game); return
        if S['phase']=='variant_warm':
            if now<S['ready'] or gt<S['game_ready']: return
            S['phase']='camera'
        if S['phase']=='camera':
            if S['view']==0:
                S['pc'].set_view_target_with_blend(S['arrival'],0)
                S['view_data']={'view':'Arrival'}
            else: S['view_data']={'view':'Guest',**near_view(game)}
            S.update(phase='settle',ready=now+3,game_ready=gt+3,deadline=now+240)
            save(); return
        if S['phase']=='settle':
            if now<S['ready'] or gt<S['game_ready']: return
            path=OUT/(VARIANTS[S['variant']][0]+'_'+S['view_data']['view']+'.png')
            unreal.SystemLibrary.execute_console_command(game,f'HighResShot 1280x800 filename="{path.as_posix()}"')
            S.update(phase='capture',path=path,requested=time.time()); return
        if S['phase']=='capture':
            path=S['path']
            if not path.exists() or path.stat().st_mtime<S['requested']-1: return
            blob=path.read_bytes()
            assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(1280,800)
            REPORT['captures'].append({'variant':VARIANTS[S['variant']][0],'path':str(path),
                'game_seconds':gt,'view':S['view_data'],'mass_diagnostics':list(unreal.CarnivalCrowdEditorLibrary.describe_live_mass_simulation(game))})
            if S['view']==0: S.update(view=1,phase='camera'); save(); return
            S['variant']+=1
            if S['variant']==len(VARIANTS): finish()
            else: apply_variant(game)
    except Exception: finish(traceback.format_exc())
    finally: S['busy']=False

save()
entry=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in ('Editor.AsyncAssetCompilationMaxConcurrency 1','Editor.AsyncStaticMeshCompilationMaxConcurrency 1',
                'Editor.AsyncSkinnedAssetCompilationMaxConcurrency 1','Editor.AsyncTextureCompilationMaxConcurrency 1',
                'Editor.AsyncAssetCompilationMaxMemoryUsage 4'):
    unreal.SystemLibrary.execute_console_command(entry,command)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
camera=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector())
camera.set_actor_label('NightFillComparisonCamera')
handle=unreal.register_slate_post_tick_callback(tick)
LE.editor_request_begin_play()
