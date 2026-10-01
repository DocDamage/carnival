"""Compare actual outfit, opaque override and source shirt in transient PIE."""
import hashlib,json,os,struct,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs'/os.environ.get('CARNIVAL_OUTFIT_REPORT','DeanOutfitIsolation_20260930');OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'capture_success':False,'errors':[],'captures':[],'assets_saved':False,'visual_review':'pending',
 'limits':'Isolated actual assembled Dean under common lighting, source static shirt of a preset body and transient material overrides. Animation cases identify their source and fixed times. Does not establish continuous walking fit, other crowd identities, GPU instances, other LODs or performance.'}
sourcepath='/Game/Outfits/TshirtVariants/OA_TshirtLngSlv/Meshes/m_med_ovw_TshirtLngSlv_nrm_lod0_mesh'
files=[ROOT/'Content'/(sourcepath.removeprefix('/Game/')+'.uasset'),ROOT/'Content/Carnival/Crowd/Collections/DA_CarnivalCrowd_G1_FINAL2.uasset']
REPORT['package_hashes_before']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
instance_path=os.environ.get('CARNIVAL_OUTFIT_INSTANCE','/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean')
assert instance_path.startswith(('/Game/Carnival/Crowd/Instances/','/Game/Carnival/Crowd/BodySurfaceProof/','/Game/Carnival/Crowd/ClothingFamilies/'))
REPORT['instance']=instance_path
if '/BodySurfaceProof/' in instance_path:
 for suffix in ('MHI_', 'DA_'):
  package=instance_path.rsplit('/',1)[0]+'/'+suffix+instance_path.rsplit('/',1)[1].removeprefix('MHI_')
  file=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset');assert file.exists();files.append(file)
 REPORT['package_hashes_before']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
instance=unreal.load_asset(instance_path);assert instance
if '/ClothingFamilies/' in instance_path:
 for obj in (instance,instance.get_meta_human_collection()):
  package=obj.get_path_name().split('.')[0]
  file=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset');assert file.exists();files.append(file)
 REPORT['package_hashes_before']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
crowd,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'DeanOutfitProof',unreal.Vector(),unreal.Rotator())
assert crowd and not error,error
source=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector());source.set_actor_label('SourceShirtProof')
source.static_mesh_component.set_static_mesh(unreal.load_asset(sourcepath));source.set_actor_hidden_in_game(True)
opaque=unreal.load_asset('/Engine/EngineMaterials/DefaultMaterial');assert opaque
light=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(150,250,250),unreal.Rotator(pitch=-20,yaw=-120))
lc=light.get_component_by_class(unreal.RectLightComponent);lc.set_mobility(unreal.ComponentMobility.MOVABLE)
for k,v in {'intensity':50,'attenuation_radius':2000,'source_width':400,'source_height':400}.items():lc.set_editor_property(k,v)
fill=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(150,-180,180))
fl=fill.get_component_by_class(unreal.PointLightComponent);fl.set_mobility(unreal.ComponentMobility.MOVABLE)
for k,v in {'intensity':20,'attenuation_radius':2000,'cast_shadows':False}.items():fl.set_editor_property(k,v)
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(100,500,100));camera.set_actor_label('OutfitProofCamera')
actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(1000,0,200))
modes=os.environ.get('CARNIVAL_OUTFIT_PROOF_MODES','FullCrowd,ShirtOnly,ShirtOpaque,SourceShirt,SourceOpaque').split(',')
assert set(modes)<={'FullCrowd','ShirtOnly','ShirtOpaque','SourceShirt','SourceOpaque','BodyOnly','BodyOpaque','FullSkinOpaque','FullBodyVisible','TrimmedBodyVisible','TrimmedBodyOnly','TrimmedOutfitSilhouette'}
SHOTS=[(mode,side) for mode in modes for side in ('Front','Back')]
S={'phase':'setup','deadline':time.monotonic()+900,'busy':False,'index':0,'components':[],'shirt_materials':[],'skin_materials':[]}
def save():
 REPORT['phase']=S['phase'];(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def finish(error=None):
 if error:REPORT['errors'].append(error)
 REPORT['package_hashes_after']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 if REPORT['package_hashes_after']!=REPORT['package_hashes_before']:REPORT['errors'].append('A reference package changed during the read-only comparison')
 REPORT['capture_success']=not REPORT['errors'] and len(REPORT['captures'])==len(SHOTS)
 REPORT['success']=REPORT['capture_success'];save()
 if S.get('pc') and S.get('previous_view'):S['pc'].set_view_target_with_blend(S['previous_view'],0)
 # Release every PIE actor/component/material wrapper before ending its world.
 # A clean later exit would not establish the cause of prior native failures.
 S.clear();S.update(phase='exit',deadline=time.monotonic()+4,busy=True)
 LE.editor_request_end_play()
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
   allactors=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
   for key,label in [('crowd','DeanOutfitProof'),('source','SourceShirtProof'),('camera','OutfitProofCamera')]:S[key]=next(a for a in allactors if a.get_actor_label()==label)
   S['pc']=pc;S['previous_view']=pc.get_view_target()
   if pc.get_hud():pc.get_hud().set_editor_property('show_hud',False)
   pawn=unreal.GameplayStatics.get_player_pawn(game,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   cc=S['camera'].camera_component;pp=cc.get_editor_property('post_process_settings')
   for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
    'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_auto_exposure_apply_physical_camera_exposure':True,
    'auto_exposure_apply_physical_camera_exposure':False,'override_bloom_intensity':True,'bloom_intensity':0.}.items():pp.set_editor_property(k,v)
   cc.set_editor_property('post_process_settings',pp);cc.set_editor_property('post_process_blend_weight',1.)
   pc.set_view_target_with_blend(S['camera'],0)
   REPORT['components']=[]
   for comp in S['crowd'].get_components_by_class(unreal.MeshComponent):
    S['components'].append((comp,comp.is_visible()))
    if isinstance(comp,unreal.SkeletalMeshComponent):
     if comp.get_name()=='Body':
      comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE);comp.set_animation(None)
     comp.set_forced_lod(1)
     REPORT['components'].append({'name':comp.get_name(),'mesh':comp.get_editor_property('skeletal_mesh_asset').get_path_name() if comp.get_editor_property('skeletal_mesh_asset') else None,
       'initial_visibility':S['components'][-1][1],
       'materials':[comp.get_material(i).get_path_name() if comp.get_material(i) else None for i in range(comp.get_num_materials())]})
    if comp.get_name()=='Outfit':
     S['shirt']=comp;S['shirt_materials']=[comp.get_material(i) for i in range(comp.get_num_materials())]
    if comp.get_name().startswith('Outfit'):
     S.setdefault('outfit_materials',[]).extend((comp,i,comp.get_material(i)) for i in range(comp.get_num_materials()))
    for i in range(comp.get_num_materials()):
     mat=comp.get_material(i)
     if mat and 'Skin_Body' in mat.get_name():S['skin_materials'].append((comp,i,mat))
   assert S.get('shirt') and len(S['shirt_materials'])==2
   S['body']=next(c for c,_ in S['components'] if c.get_name()=='Body')
   S['source_body']=S['body'].get_editor_property('skeletal_mesh_asset')
   if os.environ.get('CARNIVAL_OUTFIT_BODY_ANIMATION'):
    animation_name=os.environ['CARNIVAL_OUTFIT_BODY_ANIMATION'];assert animation_name in ('MM_Idle','MM_Walk_InPlace')
    S['animation']=unreal.load_asset('/Game/Town/Demo/Characters/Mannequins/Animations/Manny/'+animation_name);assert S['animation']
    REPORT['body_animation']=S['animation'].get_path_name();REPORT['limits']+=' Animated probe plays the current Manny source directly on the actor body; this is a compatibility diagnostic, not Mass/GPU locomotion acceptance.'
   if any(m.startswith('Trimmed') for m in modes):
    before=unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(S['source_body'])
    wardrobe_paths=['/Game/Outfits/TshirtVariants/WI_OA_TshirtLngSlv','/Game/Outfits/SlimJeansVariants/WI_OA_Jeans_slm','/Game/Outfits/CasualSneakers/WI_OA_CasualSneakers']
    garments=[unreal.load_asset(p) for p in wardrobe_paths];assert all(garments)
    REPORT['garment_masks']=[]
    for garment in garments:
     pipeline=garment.get_editor_property('Pipeline').get_editor_property('EditorPipeline')
     mask=pipeline.get_editor_property('BodyHiddenFaceMapTexture');tex=mask.get_editor_property('Texture');settings=mask.get_editor_property('Settings')
     REPORT['garment_masks'].append({'wardrobe':garment.get_path_name(),'pipeline':pipeline.get_path_name(),'texture':tex.get_path_name(),
      'settings':{k:settings.get_editor_property(k) for k in ('MaxCullValue','MinKeepValue','MaxShrinkDistance')}})
     for obj in (garment,tex):
      package=obj.get_path_name().split('.')[0]
      if package.startswith('/Game/'):
       file=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset')
       if file not in files:files.append(file);REPORT['package_hashes_before'][str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
    S['trimmed_body'],error=unreal.CarnivalCrowdMaterialEditorLibrary.make_trimmed_body_proof(S['source_body'],garments)
    assert S['trimmed_body'] and not error,error
    after=unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(S['source_body']);assert before==after
    REPORT['trimmed_body_proof']={'source':S['source_body'].get_path_name(),'garments':wardrobe_paths,'source_digest_before':before,'source_digest_after':after,
      'geometry':json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_loaded_mesh_sections(S['trimmed_body']))}
   if 'TrimmedOutfitSilhouette' in modes:
    mat=unreal.Material();S['silhouette_material']=mat
    two_sided=os.environ.get('CARNIVAL_OUTFIT_TWO_SIDED','1')=='1'
    for k,v in {'shading_model':unreal.MaterialShadingModel.MSM_UNLIT,'blend_mode':unreal.BlendMode.BLEND_OPAQUE,
      'two_sided':two_sided,'used_with_skeletal_mesh':True}.items():mat.set_editor_property(k,v)
    node=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector)
    node.set_editor_property('constant',unreal.LinearColor(.5,.5,.5,1.))
    assert unreal.MaterialEditingLibrary.connect_material_property(node,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    REPORT['silhouette_material']={'transient':True,'opaque':True,'unlit':True,'two_sided':two_sided,'skeletal_usage':True,'assets_saved':False}
   S['source_material']=S['source'].static_mesh_component.get_material(0)
   unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
   S.update(phase='position',ready=now+20);save();return
  if now<S.get('ready',0):return
  if S['phase']=='position':
   mode,side=SHOTS[S['index']];is_source=mode.startswith('Source')
   if S.get('body'):S['body'].set_skeletal_mesh_asset(S['trimmed_body'] if mode.startswith('Trimmed') else S['source_body'])
   if S.get('animation'):
    S['body'].play_animation(S['animation'],True)
    if os.environ.get('CARNIVAL_OUTFIT_ANIM_TIME'):
     pose_time=float(os.environ['CARNIVAL_OUTFIT_ANIM_TIME']);assert 0<=pose_time<S['animation'].get_play_length()
     S['body'].set_position(pose_time,False);S['body'].set_play_rate(0.)
     REPORT['fixed_animation_time']=pose_time
   S['source'].set_actor_hidden_in_game(not is_source);S['crowd'].set_actor_hidden_in_game(is_source)
   for comp,visible in S['components']:
    comp.set_visibility(visible or comp.get_name()=='Body' if mode in ('FullBodyVisible','TrimmedBodyVisible','TrimmedOutfitSilhouette') else visible if mode in ('FullCrowd','FullSkinOpaque') else comp.get_name()=='Body' if mode in ('BodyOnly','BodyOpaque','TrimmedBodyOnly') else comp==S['shirt'],False)
   for comp,i,old in S['outfit_materials']:comp.set_material(i,S['silhouette_material'] if mode=='TrimmedOutfitSilhouette' else old)
   if mode!='TrimmedOutfitSilhouette':
    for i,old in enumerate(S['shirt_materials']):S['shirt'].set_material(i,opaque if mode=='ShirtOpaque' else old)
    for comp,i,old in S['skin_materials']:comp.set_material(i,opaque if mode in ('BodyOpaque','FullSkinOpaque') else old)
   S['source'].static_mesh_component.set_material(0,opaque if mode=='SourceOpaque' else S['source_material'])
   full=mode in ('FullCrowd','FullSkinOpaque','BodyOnly','BodyOpaque','FullBodyVisible','TrimmedBodyVisible','TrimmedBodyOnly','TrimmedOutfitSilhouette');focus=unreal.Vector(0,0,90 if full else 135)
   S['camera'].camera_component.set_field_of_view(35 if full else 30)
   S['camera'].set_actor_location(focus+unreal.Vector(100,600 if full else 325,20) * unreal.Vector(1,1 if side=='Front' else -1,1),False,True)
   S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(S['camera'].get_actor_location(),focus),True)
   S.update(phase='request',ready=now+5);return
  if S['phase']=='request':
   mode,side=SHOTS[S['index']];S['image']=OUT/(mode+'_'+side+'.png');S['requested']=time.time()
   unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x800 filename="'+S['image'].as_posix()+'"')
   S.update(phase='capture',ready=now+.5);return
  if S['phase']=='capture':
   image=S['image']
   if not image.exists() or image.stat().st_mtime<S['requested']-1:return
   blob=image.read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(1280,800)
   mode,side=SHOTS[S['index']];REPORT['captures'].append({'mode':mode,'side':side,'png':str(image),'camera':list(S['camera'].get_actor_location().to_tuple()),
    'body_sockets':{bone:list(S['body'].get_socket_location(bone).to_tuple()) for bone in ('pelvis','head','hand_l','hand_r','foot_l','foot_r')},
    'body_animation_position':S['body'].get_position()})
   S['index']+=1;save()
   if S['index']==len(SHOTS):finish()
   else:S['phase']='position'
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
handle=unreal.register_slate_post_tick_callback(tick);save();LE.editor_request_begin_play()
