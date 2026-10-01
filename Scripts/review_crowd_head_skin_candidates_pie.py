"""Isolated actual crowd actor comparisons; transient candidate materials only."""
import json,os,struct,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs'/os.environ.get('CARNIVAL_SKIN_CANDIDATE_REPORT','CrowdHeadSkinCandidates_20260930')
OUT.mkdir(parents=True,exist_ok=True)
NAMES=['Kate','MHC_Advika','Petra','MHC_Hannah','MHC_Kabir','Mason','MHC_Crowd84','MHC_Seo','Skye',
       'AmandaBlack','MHC_Natasha','Skotukeda3','Skotukeda4','MHC_Base_Female']
if os.environ.get('CARNIVAL_SKIN_PROOF_HEADS'):
    requested=os.environ['CARNIVAL_SKIN_PROOF_HEADS'].split(',');assert requested and set(requested)<=set(NAMES)
    NAMES=requested
REPORT={'success':False,'capture_success':False,'errors':[],'captures':[],'candidates':{},'visual_review':'pending',
        'assets_saved':False,'limits':'Actual crowd actor head only, forced near LOD, hidden body and other actors, common isolated lighting. Does not establish full-body fit, GPU instance/other LOD appearance, population lighting or performance.'}
(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
for name in NAMES:
    proof=json.loads((ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBakes_20260930'/name/'index.json').read_text())
    reload=json.loads((ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBakes_20260930'/name/'Reload.json').read_text())
    assert proof['success'] and reload['success'] and not proof['errors'] and not reload['errors']
    instance=unreal.load_asset('/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_'+name);assert instance,name
    actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'HeadSkinProof_'+name,unreal.Vector(),unreal.Rotator())
    assert actor and not error,error
    actor.set_actor_hidden_in_game(True)
    REPORT['candidates'][name]={'instance':instance.get_path_name(),'textures':proof['saved_textures'],'material_origins':[]}
light=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(150,250,250),unreal.Rotator(pitch=-20,yaw=-120))
lc=light.get_component_by_class(unreal.RectLightComponent);lc.set_mobility(unreal.ComponentMobility.MOVABLE)
lc.set_editor_property('intensity',50);lc.set_editor_property('attenuation_radius',2000)
lc.set_editor_property('source_width',400);lc.set_editor_property('source_height',400)
fill=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(150,-180,180))
fl=fill.get_component_by_class(unreal.PointLightComponent);fl.set_mobility(unreal.ComponentMobility.MOVABLE)
fl.set_editor_property('intensity',20);fl.set_editor_property('attenuation_radius',2000);fl.set_editor_property('cast_shadows',False)
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(100,250,170));camera.set_actor_label('SkinRosterCamera')
actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(1000,0,200))
S={'phase':'setup','deadline':time.monotonic()+1800,'busy':False,'index':0,'actors':{},'materials':{}}
SHOTS=[(name,variant) for name in NAMES for variant in ('Baseline','Candidate','BaselineOpposite','CandidateOpposite')]
def save():
    REPORT['phase']=S['phase'];(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def finish(error=None):
    if error:REPORT['errors'].append(error)
    REPORT['capture_success']=not REPORT['errors'] and len(REPORT['captures'])==len(SHOTS)
    REPORT['success']=REPORT['capture_success']
    save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+4)
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
            if pc.get_hud():pc.get_hud().set_editor_property('show_hud',False)
            pawn=unreal.GameplayStatics.get_player_pawn(game,0)
            if pawn:pawn.set_actor_hidden_in_game(True)
            allactors=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
            S['camera']=next(a for a in allactors if a.get_actor_label()=='SkinRosterCamera')
            cc=S['camera'].camera_component;cc.set_field_of_view(30)
            pp=cc.get_editor_property('post_process_settings')
            for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
                'override_auto_exposure_bias':True,'auto_exposure_bias':0.,
                'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,
                'override_bloom_intensity':True,'bloom_intensity':0.}.items():pp.set_editor_property(k,v)
            cc.set_editor_property('post_process_settings',pp);cc.set_editor_property('post_process_blend_weight',1.)
            pc.set_view_target_with_blend(S['camera'],0)
            ml=unreal.MaterialEditingLibrary
            for name in NAMES:
                actor=next(a for a in allactors if a.get_actor_label()=='HeadSkinProof_'+name)
                actor.set_actor_hidden_in_game(True);S['actors'][name]=actor;S['materials'][name]=[]
                for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
                    isface=False
                    for i in range(comp.get_num_materials()):
                        old=comp.get_material(i)
                        if not old or 'head_' not in old.get_name().lower():continue
                        origin=old
                        while isinstance(origin,unreal.MaterialInstance):
                            if origin.get_name().startswith('MI_Face_'+name+'_head_'):break
                            origin=origin.get_editor_property('parent')
                        else:raise RuntimeError('Unexpected head source for '+name+': '+old.get_path_name())
                        REPORT['candidates'][name]['material_origins'].append(origin.get_path_name())
                        REPORT['candidates'][name].setdefault('component_diagnostics',[]).append({
                            'component':comp.get_path_name(),'mesh':comp.get_editor_property('skeletal_mesh_asset').get_path_name(),
                            'world_location':list(comp.get_world_location().to_tuple()),
                            'world_scale':list(comp.get_world_scale().to_tuple()),
                            'head_bone_location':list(comp.get_socket_location('head').to_tuple()),
                            'hidden_in_game':comp.get_editor_property('hidden_in_game'),
                            'visible_before':comp.is_visible()})
                        isface=True
                        clone=unreal.MaterialInstanceConstant()
                        parent=old.get_editor_property('parent') if isinstance(old,unreal.MaterialInstanceDynamic) else old
                        ml.set_material_instance_parent(clone,parent)
                        if isinstance(old,unreal.MaterialInstanceDynamic):
                            for n in ml.get_texture_parameter_names(old):
                                texture=old.get_texture_parameter_value(n)
                                if texture:ml.set_material_instance_texture_parameter_value(clone,n,texture)
                            for n in ml.get_scalar_parameter_names(old):ml.set_material_instance_scalar_parameter_value(clone,n,old.get_scalar_parameter_value(n))
                            for n in ml.get_vector_parameter_names(old):ml.set_material_instance_vector_parameter_value(clone,n,old.get_vector_parameter_value(n))
                        for row in REPORT['candidates'][name]['textures']:
                            texture=unreal.load_asset(row['asset']);assert texture
                            ml.set_material_instance_texture_parameter_value(clone,row['parameter'],texture)
                            assert ml.get_material_instance_texture_parameter_value(clone,row['parameter'])==texture
                        ml.set_material_instance_static_switch_parameter_value(clone,'Use Baked Material',True)
                        assert ml.get_material_instance_static_switch_parameter_value(clone,'Use Baked Material')
                        ml.update_material_instance(clone);S['materials'][name].append((comp,i,old,clone))
                    comp.set_visibility(isface,isface)
                    if isface:comp.set_forced_lod(1)
                assert S['materials'][name],'No actual head material for '+name
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
            S.update(phase='position',ready=now+20);save();return
        if now<S.get('ready',0):return
        if S['phase']=='position':
            name,variant=SHOTS[S['index']]
            for other,actor in S['actors'].items():actor.set_actor_hidden_in_game(other!=name)
            for comp,i,old,clone in S['materials'][name]:comp.set_material(i,clone if variant.startswith('Candidate') else old)
            focus=S['materials'][name][0][0].get_socket_location('head')
            S['camera'].set_actor_location(focus+unreal.Vector(100,-250 if variant.endswith('Opposite') else 250,10),False,True)
            S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(S['camera'].get_actor_location(),focus),True)
            S.update(phase='request',ready=now+5);return
        if S['phase']=='request':
            name,variant=SHOTS[S['index']]
            S['image']=OUT/(name+'_'+variant+'.png');S['requested']=time.time()
            unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x800 filename="'+S['image'].as_posix()+'"')
            S.update(phase='capture',ready=now+.5);return
        if S['phase']=='capture':
            image=S['image']
            if not image.exists() or image.stat().st_mtime<S['requested']-1:return
            blob=image.read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(1280,800)
            name,variant=SHOTS[S['index']]
            REPORT['captures'].append({'head':name,'variant':variant,'png':str(image),
                'camera':list(S['camera'].get_actor_location().to_tuple()),'materials':len(S['materials'][name])})
            S['index']+=1;save()
            if S['index']==len(SHOTS):finish()
            else:S['phase']='position'
    except Exception:finish(traceback.format_exc())
    finally:S['busy']=False
handle=unreal.register_slate_post_tick_callback(tick);save();LE.editor_request_begin_play()
