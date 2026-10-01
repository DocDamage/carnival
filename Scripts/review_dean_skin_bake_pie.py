"""Render an isolated, unsaved source/crowd/bake comparison in ordinary PIE."""
import json,struct,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()).resolve()
exec(compile((ROOT/'Scripts/bake_dean_skin_proof.py').read_text(),str(ROOT/'Scripts/bake_dean_skin_proof.py'),'exec'),globals())
OUT=ROOT/'Saved/CharacterRepairs/DeanSkinRenderedProof_20260930'
OUT.mkdir(parents=True,exist_ok=True)
REPORT['success']=False;REPORT['captures']=[];REPORT['visual_review']='pending'
REPORT['limits']='Isolated temporary source face and actual Dean crowd actor variant under common lighting. No saved crowd changes or instanced/full-world/LOD acceptance.'
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
source=actors.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector())
source.set_actor_label('SourceSkinReference')
source.skeletal_mesh_component.set_skeletal_mesh_asset(face)
# Both meshes face +Y in the reference pose; retain that common orientation.
source.set_actor_rotation(unreal.Rotator(),True)
instance=unreal.load_asset('/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean')
crowd,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'DeanCrowdProof',unreal.Vector(),unreal.Rotator())
assert crowd and not error,error
light=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(150,250,250),unreal.Rotator(pitch=-20,yaw=-120))
lc=light.get_component_by_class(unreal.RectLightComponent)
lc.set_mobility(unreal.ComponentMobility.MOVABLE)
lc.set_editor_property('intensity',50);lc.set_editor_property('attenuation_radius',2000)
lc.set_editor_property('source_width',400);lc.set_editor_property('source_height',400)
fill=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(150,-180,180))
fl=fill.get_component_by_class(unreal.PointLightComponent);fl.set_mobility(unreal.ComponentMobility.MOVABLE)
fl.set_editor_property('intensity',20);fl.set_editor_property('attenuation_radius',2000)
fl.set_editor_property('cast_shadows',False)
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(100,250,170))
camera.set_actor_label('SkinProofCamera')
actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(1000,0,200))
S={'phase':'setup','deadline':time.monotonic()+600,'busy':False,'index':0,'materials':[]}
SHOTS=['CrowdBaseline','SourceReference','CrowdBakedCandidate',
       'CrowdBaselineOpposite','SourceReferenceOpposite','CrowdBakedCandidateOpposite']
def save():
    REPORT['phase']=S['phase'];(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def finish(error=None):
    if error:REPORT['errors'].append(error)
    REPORT['capture_success']=not REPORT['errors'] and len(REPORT['captures'])==len(SHOTS)
    REPORT['success']=False
    save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+4)
def tick(_):
    if S['busy']:return
    S['busy']=True
    try:
        now=time.monotonic()
        if S['phase']=='exit':
            if now>S['deadline']:unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if now>S['deadline']:raise RuntimeError('Timed out in '+S['phase'])
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:return
        if S['phase']=='setup':
            allactors=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
            S['source']=next(a for a in allactors if a.get_actor_label()=='SourceSkinReference')
            S['crowd']=next(a for a in allactors if a.get_actor_label()=='DeanCrowdProof')
            S['camera']=next(a for a in allactors if a.get_actor_label()=='SkinProofCamera')
            pc=unreal.GameplayStatics.get_player_controller(game,0)
            if not pc:return
            if pc.get_hud():pc.get_hud().set_editor_property('show_hud',False)
            pawn=unreal.GameplayStatics.get_player_pawn(game,0)
            if pawn:pawn.set_actor_hidden_in_game(True)
            cc=S['camera'].camera_component;cc.set_field_of_view(30)
            pp=cc.get_editor_property('post_process_settings')
            for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
                'override_auto_exposure_bias':True,'auto_exposure_bias':0.,
                'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,
                'override_bloom_intensity':True,'bloom_intensity':0.}.items():pp.set_editor_property(k,v)
            cc.set_editor_property('post_process_settings',pp);cc.set_editor_property('post_process_blend_weight',1.)
            S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(S['camera'].get_actor_location(),unreal.Vector(0,0,160)),True)
            pc.set_view_target_with_blend(S['camera'],0)
            REPORT['crowd_components']=[]
            ml=unreal.MaterialEditingLibrary
            for comp in S['crowd'].get_components_by_class(unreal.SkeletalMeshComponent):
                row={'mesh':comp.get_editor_property('skeletal_mesh_asset').get_path_name() if comp.get_editor_property('skeletal_mesh_asset') else None,
                    'component':comp.get_path_name(),'materials':[]}
                REPORT['crowd_components'].append(row)
                isface=False
                for i in range(comp.get_num_materials()):
                    old=comp.get_material(i);row['materials'].append(path(old))
                    if not old or 'head_' not in old.get_name().lower():continue
                    isface=True
                    clone=unreal.MaterialInstanceConstant()
                    # Constant instances cannot inherit a runtime dynamic instance.
                    parent=old.get_editor_property('parent') if isinstance(old,unreal.MaterialInstanceDynamic) else old
                    ml.set_material_instance_parent(clone,parent)
                    row['proof_parent']=path(parent)
                    if isinstance(old,unreal.MaterialInstanceDynamic):
                        for n in ml.get_texture_parameter_names(old):
                            texture=old.get_texture_parameter_value(n)
                            if texture:ml.set_material_instance_texture_parameter_value(clone,n,texture)
                        for n in ml.get_scalar_parameter_names(old):ml.set_material_instance_scalar_parameter_value(clone,n,old.get_scalar_parameter_value(n))
                        for n in ml.get_vector_parameter_names(old):ml.set_material_instance_vector_parameter_value(clone,n,old.get_vector_parameter_value(n))
                    for g in REPORT['graphs']:
                        for tex in g['textures']:
                            texture=unreal.load_object(None,tex['asset']);assert texture,tex['asset']
                            # Installed library mutates correctly but returns false unconditionally.
                            ml.set_material_instance_texture_parameter_value(clone,tex['parameter'],texture)
                            assert ml.get_material_instance_texture_parameter_value(clone,tex['parameter'])==texture,tex['parameter']+' on '+path(parent)
                    ml.set_material_instance_static_switch_parameter_value(clone,'Use Baked Material',True)
                    assert ml.get_material_instance_static_switch_parameter_value(clone,'Use Baked Material')
                    ml.update_material_instance(clone)
                    S['materials'].append((comp,i,old,clone))
                if not isface:comp.set_visibility(False,False)
                else:
                    comp.set_visibility(True,True)
                    comp.set_forced_lod(1)
            assert S['materials'],'No crowd head materials found'
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
            S.update(phase='position',ready=now+20);save();return
        if now<S.get('ready',0):return
        if S['phase']=='position':
            shot=SHOTS[S['index']]
            S['camera'].set_actor_location(unreal.Vector(100,250 if S['index']<3 else -250,170),False,True)
            S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(S['camera'].get_actor_location(),unreal.Vector(0,0,160)),True)
            reference=shot.startswith('SourceReference')
            S['source'].set_actor_hidden_in_game(not reference)
            S['crowd'].set_actor_hidden_in_game(reference)
            for comp,i,old,clone in S['materials']:comp.set_material(i,clone if shot.startswith('CrowdBakedCandidate') else old)
            S.update(phase='request',ready=now+5);return
        if S['phase']=='request':
            S['image']=OUT/(SHOTS[S['index']]+'.png');S['requested']=time.time()
            unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x800 filename="'+S['image'].as_posix()+'"')
            S.update(phase='capture',ready=now+.5);return
        if S['phase']=='capture':
            image=S['image']
            if not image.exists() or image.stat().st_mtime<S['requested']-1:return
            blob=image.read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(1280,800)
            REPORT['captures'].append({'variant':SHOTS[S['index']],'png':str(image),
                'crowd_hidden':S['crowd'].get_editor_property('hidden'),
                'camera_location':list(S['camera'].get_actor_location().to_tuple()),
                'camera_rotation':list(S['camera'].get_actor_rotation().to_tuple()),
                'source_rotation':list(S['source'].get_actor_rotation().to_tuple()),
                'crowd_bounds':str(S['crowd'].get_actor_bounds(False)),
                'source_bounds':str(S['source'].get_actor_bounds(False)),
                'head_components':[{'component':comp.get_path_name(),'visible':comp.is_visible()}
                    for comp,i,old,clone in S['materials']]})
            S['index']+=1;save()
            if S['index']==len(SHOTS):finish()
            else:S['phase']='position'
    except Exception:finish(traceback.format_exc())
    finally:S['busy']=False
handle=unreal.register_slate_post_tick_callback(tick);save();LE.editor_request_begin_play()
