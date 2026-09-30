"""Render saved child guest assets and evaluated poses in an unsaved lit preview.

The ordinary guest Blueprint/capsule is exercised in PIE. This is an isolated
asset review, not world placement, navigation, a fitted ride seat or performance.
"""
import json,os,struct,time,traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildPreview';OUT.mkdir(parents=True,exist_ok=True)
COMPARISON=os.environ.get('CARNIVAL_CHILD_REFERENCE_COMPARISON')=='1'
CANDIDATE=os.environ.get('CARNIVAL_CHILD_CONSISTENT_BIND')=='1'
FACE_PREVIEW=os.environ.get('CARNIVAL_CHILD_FACE_PREVIEW')=='1'
VARIANT=os.environ.get('CARNIVAL_CHILD_PREVIEW_VARIANT','')
assert VARIANT in ('','FixedExposure','DX11FixedExposure','DX11FixedExposureEV3'),VARIANT
assert sum((COMPARISON,CANDIDATE,FACE_PREVIEW))<=1,'Choose one comparison mode'
if COMPARISON:
    OUT=OUT/'BlackBoyReferenceAlignment';OUT.mkdir(parents=True,exist_ok=True)
if CANDIDATE:
    OUT=OUT/'BlackBoyConsistentBind';OUT.mkdir(parents=True,exist_ok=True)
if FACE_PREVIEW:
    OUT=OUT/('FaceCloseups'+VARIANT);OUT.mkdir(parents=True,exist_ok=True)
source=json.loads((ROOT/'Saved/CharacterAcceptance/ChildSources/Child_Guest_Blueprints.json').read_text());assert source['success']
if CANDIDATE:
    original_blackboy_mesh=next(c['mesh'] for c in source['children'] if c['identity']=='BlackBoy')
    candidate=json.loads((ROOT/'Saved/CharacterAcceptance/ChildSources/BlackBoy_ConsistentBind_Guest.json').read_text());assert candidate['success']
    source['children']=[candidate['children'][0] if c['identity']=='BlackBoy' else c for c in source['children']]
REPORT={'success':False,'errors':[],'children':[],'captures':[],'visual_review':'pending',
    'limits':'Isolated unsaved lit preview of actual saved guest assets. Clips pause at measured sample times. No roaming, full clothing fit across motion, fitted ride seats, populated-world or packaged-performance acceptance.'}
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
S={'phase':'setup','deadline':time.monotonic()+1200,'busy':False,'index':0}
SHOTS=[(identity,pose) for identity in ('BlackGirl','WhiteBoy','WhiteGirl','BlackBoy') for pose in ('Reference','Idle','Walk','SeatedSource')]
if COMPARISON:SHOTS=[('BlackBoy','Reference'),('BlackBoy','Idle')]
if CANDIDATE:SHOTS=[('BlackBoy',pose) for pose in ('Reference','Idle','Walk','SeatedSource')]
if FACE_PREVIEW:SHOTS=[(identity,'Idle') for identity in ('BlackGirl','WhiteBoy','WhiteGirl','BlackBoy')]

def save():
    REPORT['phase']=S['phase'];(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))

def finish(error=None):
    if error:REPORT['errors'].append(error)
    REPORT['success']=not REPORT['errors'] and len(REPORT['captures'])==len(SHOTS)
    save();LE.editor_request_end_play();S.update(phase='exit',deadline=time.monotonic()+4)

def tick(_):
    if S['busy']:return
    S['busy']=True
    try:
        now=time.monotonic()
        if S['phase']=='exit':
            if now>S['deadline']:unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
            return
        if now>S['deadline']:raise RuntimeError('Timeout during '+S['phase'])
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:return
        if S['phase']=='setup':
            pc=unreal.GameplayStatics.get_player_controller(game,0)
            if not pc:return
            unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
            unreal.SystemLibrary.execute_console_command(game,'viewmode lit')
            unreal.SystemLibrary.execute_console_command(game,'r.EyeAdaptationQuality 2')
            if pc.get_hud():pc.get_hud().set_editor_property('show_hud',False)
            pawn=unreal.GameplayStatics.get_player_pawn(game,0)
            if pawn:pawn.set_actor_hidden_in_game(True)
            REPORT['player_hidden_for_isolated_asset_views']=True
            guests={}
            for child in source['children']:
                identity=child['identity'];matches=[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Character) if a.get_actor_label()=='Preview_'+identity]
                assert len(matches)==1,(identity,len(matches));guest=matches[0]
                body=guest.get_editor_property('mesh');capsule=guest.get_component_by_class(unreal.CapsuleComponent)
                assert body.get_editor_property('skeletal_mesh_asset').get_path_name()==child['mesh']
                physics=body.get_editor_property('skeletal_mesh_asset').get_editor_property('physics_asset')
                if identity=='BlackBoy':assert physics,'Missing saved physics dependency for '+identity
                if physics:
                    physics_path=physics.get_path_name().split('.')[0]
                    assert (ROOT/'Content'/(physics_path.removeprefix('/Game/')+'.uasset')).exists(),physics_path
                assert abs(capsule.get_scaled_capsule_half_height()-child['capsule_half_height_cm'])<.01
                if CANDIDATE and identity=='BlackBoy':
                    original=unreal.load_asset(original_blackboy_mesh)
                    actual_mesh=body.get_editor_property('skeletal_mesh_asset')
                    expected_morphs=set(original.get_all_morph_target_names())
                    actual_morphs=set(actual_mesh.get_all_morph_target_names())
                    REPORT['candidate_morphs']={'original_count':len(expected_morphs),'candidate_count':len(actual_morphs),'missing':sorted(expected_morphs-actual_morphs)}
                    assert expected_morphs==actual_morphs,REPORT['candidate_morphs']
                guests[identity]={'actor':guest,'body':body,'source':child}
                REPORT['children'].append({'identity':identity,'actual_class':guest.get_class().get_path_name(),
                    'actual_mesh':child['mesh'],'capsule_half_height_cm':capsule.get_scaled_capsule_half_height(),
                    'capsule_radius_cm':capsule.get_scaled_capsule_radius(),
                    'materials':[body.get_material(i).get_path_name() if body.get_material(i) else None for i in range(body.get_num_materials())]})
            cameras=[a for a in unreal.GameplayStatics.get_all_actors_of_class(game,unreal.CameraActor)
                     if a.get_actor_label()=='ChildPreviewCamera']
            assert len(cameras)==1
            camera=cameras[0]
            camera.get_component_by_class(unreal.CameraComponent).set_field_of_view(45)
            if 'FixedExposure' in VARIANT:
                ev=3. if VARIANT.endswith('EV3') else 1.
                component=camera.get_component_by_class(unreal.CameraComponent)
                settings=component.get_editor_property('post_process_settings')
                for name,value in {'override_auto_exposure_min_brightness':True,
                    'override_auto_exposure_max_brightness':True,
                    'override_auto_exposure_bias':True,'auto_exposure_min_brightness':ev,
                    'auto_exposure_max_brightness':ev,'auto_exposure_bias':0.}.items():
                    settings.set_editor_property(name,value)
                component.set_editor_property('post_process_settings',settings)
                component.set_editor_property('post_process_blend_weight',1.)
                REPORT['fixed_exposure']={'min_ev100':ev,'max_ev100':ev,'bias':0.,
                    'limits':'Isolated diagnostic camera exposure only; production map lighting unchanged.'}
            S.update(game=game,pc=pc,guests=guests,camera=camera,phase='warm',ready=now+15)
            save();return
        if S['phase']=='warm':
            if now<S['ready']:return
            S['phase']='camera'
        identity,pose=SHOTS[S['index']];row=S['guests'][identity];guest=row['actor'];body=row['body']
        if S['phase']=='camera':
            names={'Idle':'Child_Manny_MM_Idle','Walk':'Child_Manny_MM_Walk_InPlace','SeatedSource':'Child_SeatedSource_AS_Idle_Riding'}
            folder=row['source']['idle'].split('/Animations/')[0]
            clip=None if pose=='Reference' else unreal.load_asset(folder+'/Animations/'+names[pose])
            if COMPARISON and pose=='Idle':
                clip=unreal.load_asset('/Game/Carnival/Characters/Children/BlackBoy/Diagnostics/Comparison_MM_Idle_ReferenceAlignment')
            if pose!='Reference':assert clip
            position=clip.get_editor_property('sequence_length')*.4 if clip else 0
            # OverrideAnimationData is for serialized construction defaults. If
            # single-node mode is already active, it does not replace that live
            # instance's asset. Use playback APIs and verify its actual asset.
            body.play_animation(clip,True)
            body.set_position(position,False);body.set_play_rate(0)
            live=body.get_anim_instance();assert isinstance(live,unreal.AnimSingleNodeInstance)
            origin=guest.get_actor_location();height=row['source']['mesh_height_cm']
            focus=unreal.Vector(origin.x,origin.y,height*.5+3)
            location=focus+unreal.Vector(height*2.7,0,height*.07)
            if FACE_PREVIEW:
                focus=unreal.Vector(origin.x,origin.y,height*.90+3)
                location=focus+unreal.Vector(height*.70,0,height*.015)
            S['camera'].set_actor_location(location,False,True)
            S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location,focus),True)
            S['pc'].set_view_target_with_blend(S['camera'],0)
            S.update(phase='settle',ready=now+3,clip=clip,position=position);return
        if S['phase']=='settle':
            if now<S['ready']:return
            if FACE_PREVIEW and not S.get('face_framed'):
                eyes=['L_Eye','R_Eye'] if identity=='BlackBoy' else ['cc_base_l_eye','cc_base_r_eye']
                available={str(body.get_bone_name(i)) for i in range(body.get_num_bones())}
                assert set(eyes)<=available,(identity,eyes)
                focus=(body.get_socket_location(eyes[0])+body.get_socket_location(eyes[1]))*.5
                focus+=unreal.Vector(0,0,-3)
                height=row['source']['mesh_height_cm']
                location=focus+unreal.Vector(height*.55,0,height*.015)
                S['camera'].set_actor_location(location,False,True)
                S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location,focus),True)
                S.update(face_framed=True,face_focus=focus.to_tuple(),ready=now+3)
                return
            image=OUT/(identity+'_'+pose+'.png')
            unreal.SystemLibrary.execute_console_command(game,f'HighResShot 1280x800 filename="{image.as_posix()}"')
            S.update(phase='capture',image=image,requested=time.time());return
        if S['phase']=='capture':
            image=S['image']
            if not image.exists() or image.stat().st_mtime<S['requested']-1:return
            blob=image.read_bytes()
            assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(1280,800)
            bones=['Pelvis','Head','L_Foot','R_Foot','L_Hand','R_Hand'] if identity=='BlackBoy' else ['pelvis','head','foot_l','foot_r','hand_l','hand_r']
            actual={name:body.get_socket_location(name) for name in bones}
            errors={}
            if S['clip']:
                evaluation=unreal.AnimPoseEvaluationOptions()
                evaluation.optional_skeletal_mesh=body.get_editor_property('skeletal_mesh_asset')
                evaluation.should_retarget=True;evaluation.incorporate_root_motion_into_pose=True
                expected=unreal.AnimPoseExtensions.get_anim_pose_at_time(S['clip'],S['position'],evaluation)
                relative=body.get_relative_transform();actor_transform=guest.get_actor_transform()
                for name in bones:
                    mesh_space=expected.get_bone_pose(name,unreal.AnimPoseSpaces.WORLD).translation
                    world=unreal.MathLibrary.transform_location(actor_transform,
                        unreal.MathLibrary.transform_location(relative,mesh_space))
                    errors[name]=unreal.Vector.distance(actual[name],world)
                if max(errors.values())>5:
                    REPORT['pose_mismatch']={'identity':identity,'pose':pose,'bone_errors_cm':errors}
                    raise RuntimeError('Rendered component pose differs from requested evaluated clip by over 5 cm')
            else:
                hands=(actual[bones[4]]-actual[bones[5]]).length()
                if hands<row['source']['mesh_height_cm']*.45:
                    raise RuntimeError('Reference capture retained narrow animated hand stance')
            REPORT['captures'].append({'identity':identity,'pose':pose,'image':str(image),
                'clip':S['clip'].get_path_name() if S['clip'] else None,'sample_seconds':S['position'],
                'pose_verification':'Evaluated requested-clip world bone positions within 5 cm' if S['clip'] else 'Reference hand span positive control',
                'bone_pose_errors_cm':errors,'bone_world_cm':{name:value.to_tuple() for name,value in actual.items()}})
            runtime_materials=[]
            for i in range(body.get_num_materials()):
                material=body.get_material(i)
                if not isinstance(material,unreal.MaterialInstanceDynamic):continue
                slot=str(body.get_editor_property('skeletal_mesh_asset').materials[i].material_slot_name)
                if not any(s in slot.lower() for s in ('skin_head','hair','transparency')):continue
                runtime_materials.append({'slot':slot,'asset':material.get_path_name(),
                    'base_color_tint':material.get_vector_parameter_value('Base Color Tint').to_tuple(),
                    'scatter':material.get_scalar_parameter_value('Scatter'),
                    'specular_multiplier':material.get_scalar_parameter_value('Specular Multiplier')})
            REPORT['captures'][-1]['runtime_material_parameters']=runtime_materials
            if FACE_PREVIEW:REPORT['captures'][-1]['posed_eye_focus_cm']=S['face_focus']
            S['face_framed']=False
            S['index']+=1;save()
            if S['index']==len(SHOTS):finish()
            else:S['phase']='camera'
    except Exception:finish(traceback.format_exc())
    finally:S['busy']=False

world=unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry');assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,375,-10))
floor.set_actor_location(unreal.Vector(0,375,-10),False,True)
component=floor.get_component_by_class(unreal.StaticMeshComponent)
component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
component.set_material(0,unreal.load_asset('/Engine/BasicShapes/BasicShapeMaterial'))
component.set_collision_profile_name('BlockAll');floor.set_actor_scale3d(unreal.Vector(12,15,.2))
for index,child in enumerate(source['children']):
    cls=unreal.load_class(None,child['class']);assert cls
    actor=actors.spawn_actor_from_class(cls,unreal.Vector(0,index*250,child['capsule_half_height_cm']+3))
    actor.set_actor_location(unreal.Vector(0,index*250,child['capsule_half_height_cm']+3),False,True)
    actor.set_actor_label('Preview_'+child['identity'])
key=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(350,375,350),unreal.Rotator(pitch=-25,yaw=180,roll=0))
key.set_actor_location(unreal.Vector(350,375,350),False,True)
key.set_actor_rotation(unreal.Rotator(pitch=-25,yaw=180,roll=0),True)
light=key.get_component_by_class(unreal.RectLightComponent);light.set_mobility(unreal.ComponentMobility.MOVABLE)
light.set_editor_property('intensity',200);light.set_editor_property('attenuation_radius',2500)
light.set_editor_property('source_width',1000);light.set_editor_property('source_height',500)
fill=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(150,375,250))
fill.set_actor_location(unreal.Vector(150,375,250),False,True)
light=fill.get_component_by_class(unreal.PointLightComponent);light.set_mobility(unreal.ComponentMobility.MOVABLE)
light.set_editor_property('intensity',40);light.set_editor_property('attenuation_radius',2500)
light.set_editor_property('cast_shadows',False)
actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(800,375,110))
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(500,375,150))
camera.set_actor_label('ChildPreviewCamera')
handle=unreal.register_slate_post_tick_callback(tick);save();LE.editor_request_begin_play()
