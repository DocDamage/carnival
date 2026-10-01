"""Inspect saved Dean bindings on a real moving entity with all 240 guests retained."""
import collections,json,math,os,struct,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs'/os.environ.get('CARNIVAL_DEAN_LIVE_REPORT','DeanCrowdLiveAcceptance_20260930')
OUT.mkdir(parents=True,exist_ok=True)
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
REPORT={'success':False,'errors':[],'captures':[],'material_checks':[], 'visual_review':'pending',
        'assets_saved':False,'density_changed':False,'entities_or_player_teleported':False,
        'limits':'Transient review camera follows an actual Dean Mass identity in the complete populated world. FOV frames the target at each distance; LOD settings/budgets and simulation are untouched. Appearance review, other heads/LODs, movement/clothing and packaged performance require separate acceptance.'}
S={'phase':'setup','deadline':time.monotonic()+1800,'busy':False,'index':0}
SHOTS=[('Near',180.),('Medium',1800.),('Far',4500.),('ReturnNear',180.)]
MULTIANGLE=os.environ.get('CARNIVAL_DEAN_MULTIANGLE')=='1'
if MULTIANGLE:
    SHOTS=[('Near',180.)]+[(label+str(angle),distance) for label,distance in [('Medium',1800.),('Far',4500.)]
        for angle in range(0,360,45)]+[('ReturnNear',180.)]
REPORT['camera_clearance_mode']='Eight elevated views at each instanced distance, with a live complex trace at every follow update.' if MULTIANGLE else 'Initial camera trace only'
def save():
    REPORT['phase']=S['phase'];(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def finish(error=None):
    if error:REPORT['errors'].append(error)
    REPORT['capture_success']=not REPORT['errors'] and len(REPORT['captures'])==len(SHOTS)
    REPORT['success']=REPORT['capture_success']
    save()
    # Release transient PIE actor wrappers before world teardown. This is cleanup,
    # not a proven explanation for the late process-exit access violation.
    if S.get('pc') and S.get('arrival'):
        S['pc'].set_view_target_with_blend(S['arrival'],0)
    for key in ('pc','arrival','camera','camera_ignore'):S.pop(key,None)
    LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+4)
def entity(game):
    all=unreal.CarnivalCrowdEditorLibrary.sample_live_crowd_entities(game)
    assert len(all)==240,len(all)
    matches=[e for e in all if e.appearance_source.endswith('/MHI_Dean.MHI_Dean')]
    assert matches,'No actual Dean appearance among the 240 entities'
    if 'identity' not in S:
        # Prefer an initially separated actual guest, without changing crowd placement.
        selected=max(matches,key=lambda candidate:min(math.hypot(candidate.location.x-other.location.x,
            candidate.location.y-other.location.y) for other in all if candidate.entity_index!=other.entity_index))
        S['identity']=[selected.entity_index,selected.entity_serial]
        REPORT['selected_entity']={'identity':S['identity'],'appearance':selected.appearance_source,
            'initial_position':list(selected.location.to_tuple())}
    tracked=next(e for e in matches if [e.entity_index,e.entity_serial]==S['identity'])
    assert not unreal.GameplayStatics.is_game_paused(game)
    assert unreal.GameplayStatics.get_global_time_dilation(game)==1.
    REPORT['representation_counts']=dict(collections.Counter(e.representation_type for e in all))
    REPORT['appearance_counts']=dict(collections.Counter(e.appearance_source for e in all))
    return tracked
def aim(game,e,select_angle=False):
    distance=SHOTS[S['index']][1]
    velocity=e.velocity
    heading=math.atan2(velocity.y,velocity.x) if math.hypot(velocity.x,velocity.y)>1 else S.get('heading',0.)
    S['heading']=heading
    point=e.location;focus=point+unreal.Vector(0,0,155)
    if MULTIANGLE:
        shot=SHOTS[S['index']][0]
        angle=math.radians(int(''.join(c for c in shot if c.isdigit()) or '0'))+heading
        height=distance*(.4 if distance>1000 else .15)
        radius=math.sqrt(distance*distance-height*height)
        location=focus+unreal.Vector(math.cos(angle)*radius,math.sin(angle)*radius,height)
        # Representation changes can destroy pooled actors between frames.
        # Use a current list, never cached actor wrappers, for a native trace.
        ignore=[S['camera']]+[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
            if 'CrowdActor' in a.get_class().get_name()]
        hit=unreal.SystemLibrary.line_trace_single(game,location,focus,unreal.TraceTypeQuery.ECC_CAMERA,
            True,ignore,unreal.DrawDebugTrace.NONE,True)
        S['clearance_hit']=bool(hit and hit.to_tuple()[0])
        S['camera'].set_actor_location(location,False,True)
        S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location,focus),True)
        S['camera'].camera_component.set_field_of_view(max(2.,min(60.,math.degrees(2*math.atan(70./distance)))))
        return
    if select_angle:
        ignore=[S['camera']]+[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
            if 'CrowdActor' in a.get_class().get_name()]
        for offset in (0.,math.pi/4,-math.pi/4,math.pi/2,-math.pi/2,math.pi,3*math.pi/4,-3*math.pi/4):
            location=point+unreal.Vector(math.cos(heading+offset)*distance,math.sin(heading+offset)*distance,170+distance*.025)
            hit=unreal.SystemLibrary.line_trace_single(game,location,focus,unreal.TraceTypeQuery.ECC_CAMERA,
                False,ignore,unreal.DrawDebugTrace.NONE,True)
            if not hit or not hit.to_tuple()[0]:S['offset']=offset;break
        else:raise RuntimeError('No clear world-geometry camera ray at '+SHOTS[S['index']][0])
    location=point+unreal.Vector(math.cos(heading+S['offset'])*distance,math.sin(heading+S['offset'])*distance,170+distance*.025)
    S['camera'].set_actor_location(location,False,True)
    S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location,focus),True)
    S['camera'].camera_component.set_field_of_view(max(2.,min(60.,math.degrees(2*math.atan(70./distance)))))
def check_materials(game):
    ml=unreal.MaterialEditingLibrary
    rows=[]
    for actor in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor):
        for comp in actor.get_components_by_class(unreal.MeshComponent):
            for i in range(comp.get_num_materials()):
                mat=comp.get_material(i)
                if not mat:continue
                parent=mat
                while isinstance(parent,unreal.MaterialInstance):
                    name=parent.get_name()
                    if name.startswith(('MI_Face_Dean_','MI_FaceCombo_Dean_')):break
                    parent=parent.get_editor_property('parent')
                else:continue
                tex=mat.get_texture_parameter_value('Basecolor Baked') if isinstance(mat,unreal.MaterialInstanceDynamic) else ml.get_material_instance_texture_parameter_value(mat,'Basecolor Baked')
                assert tex and '/FaceBakeProof/Dean/' in tex.get_path_name(),mat.get_path_name()
                constant=mat.get_editor_property('parent') if isinstance(mat,unreal.MaterialInstanceDynamic) else mat
                assert ml.get_material_instance_static_switch_parameter_value(constant,'Use Baked Material')
                rows.append({'component':comp.get_path_name(),'class':comp.get_class().get_name(),
                    'material':mat.get_path_name(),'basecolor_baked':tex.get_path_name(),'use_baked_material':True})
    REPORT['material_checks'].append({'view':SHOTS[S['index']][0],'bindings':rows})
    assert rows,'No actual live Dean face material found'
def tick(_):
    if S['busy']:return
    S['busy']=True
    try:
        now=time.monotonic()
        if S['phase']=='exit':
            if now>S['deadline']:unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if now>S['deadline']:raise RuntimeError('Timeout in '+S['phase'])
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:return
        if S['phase']=='setup':
            pc=unreal.GameplayStatics.get_player_controller(game,0)
            if not pc:return
            spawners=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.MassSpawner)
            assert sum(a.get_count()*a.get_spawning_count_scale() for a in spawners)==240
            S['pc']=pc;S['arrival']=pc.get_view_target()
            S['camera']=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CameraActor) if a.get_actor_label()=='DeanLiveReviewCamera')
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
            for spawner in spawners:spawner.wait_for_streaming_assets()
            S.update(phase='warm',ready=time.monotonic()+30,game_ready=unreal.GameplayStatics.get_time_seconds(game)+20,deadline=time.monotonic()+1800)
            save();return
        if S['phase']=='warm':
            if now<S['ready'] or unreal.GameplayStatics.get_time_seconds(game)<S['game_ready']:return
            S['phase']='position'
        e=entity(game)
        if S['phase']=='position':
            aim(game,e,True);S['pc'].set_view_target_with_blend(S['camera'],0)
            S.update(phase='settle',ready=now+12,game_ready=unreal.GameplayStatics.get_time_seconds(game)+8,deadline=now+240)
            save();return
        if S['phase']=='settle':
            aim(game,e)
            if now<S['ready'] or unreal.GameplayStatics.get_time_seconds(game)<S['game_ready']:return
            check_materials(game)
            S['image']=OUT/(SHOTS[S['index']][0]+'.png');S['requested']=time.time()
            S['capture_entity']={'identity':S['identity'],'appearance':e.appearance_source,
                'position':list(e.location.to_tuple()),'velocity':list(e.velocity.to_tuple()),
                'representation_type':e.representation_type,'lane':e.lane_index,
                'camera':list(S['camera'].get_actor_location().to_tuple()),
                'camera_complex_trace_hit':S.get('clearance_hit'),
                'fov':S['camera'].camera_component.get_editor_property('field_of_view')}
            unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x800 filename="'+S['image'].as_posix()+'"')
            S['phase']='capture';return
        if S['phase']=='capture':
            image=S['image']
            if not image.exists() or image.stat().st_mtime<S['requested']-1:return
            blob=image.read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(1280,800)
            REPORT['captures'].append({'view':SHOTS[S['index']][0],'png':str(image),'entity':S['capture_entity']})
            S['index']+=1;save()
            if S['index']==len(SHOTS):finish()
            else:S['phase']='position'
    except Exception:finish(traceback.format_exc())
    finally:S['busy']=False
save()
entry=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in ('Editor.AsyncAssetCompilationMaxConcurrency 1','Editor.AsyncStaticMeshCompilationMaxConcurrency 1',
    'Editor.AsyncSkinnedAssetCompilationMaxConcurrency 1','Editor.AsyncTextureCompilationMaxConcurrency 1','Editor.AsyncAssetCompilationMaxMemoryUsage 4'):
    unreal.SystemLibrary.execute_console_command(entry,command)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
camera=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector())
camera.set_actor_label('DeanLiveReviewCamera')
handle=unreal.register_slate_post_tick_callback(tick);LE.editor_request_begin_play()
