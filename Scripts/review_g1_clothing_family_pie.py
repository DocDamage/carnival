"""Review each saved clothing-family candidate with its baked clip in transient PIE."""
import hashlib,json,os,struct,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()).resolve();OUT=ROOT/'Saved/CharacterRepairs'/os.environ.get('CARNIVAL_FAMILY_GALLERY_REPORT','G1ClothingFamilyGallery_20260930');OUT.mkdir(parents=True,exist_ok=True)
GROUP=os.environ.get('CARNIVAL_FAMILY_GROUP','G1');FAMILY=os.environ.get('CARNIVAL_CLOTHING_FAMILY','Parts')
assert GROUP in ('G1','G2','G3','G4','G5') and FAMILY in ('Parts','Complete')
FAMILY_DIR=GROUP+FAMILY+('Retargeted' if os.environ.get('CARNIVAL_CONVERT_BODY_ANIMATIONS')=='1' else '')
FAMILY_DIR += 'LOD0' if os.environ.get('CARNIVAL_FAMILY_BODY_SOURCE_LOD')=='0' else ''
ANIMATION=os.environ.get('CARNIVAL_FAMILY_GALLERY_ANIMATION','Idle');assert ANIMATION in ('Idle','Walk','Reference')
DRIVE_OUTFIT=os.environ.get('CARNIVAL_GALLERY_DRIVE_OUTFIT')=='1'
ACTOR_HAIR=os.environ.get('CARNIVAL_GALLERY_ACTOR_HAIR')=='1'
FOLLOW_BODY=os.environ.get('CARNIVAL_GALLERY_OUTFIT_FOLLOW_BODY')=='1'
OWNED_ACTOR=os.environ.get('CARNIVAL_GALLERY_OWNED_ACTOR')=='1'
SOURCE_HAIR=os.environ.get('CARNIVAL_GALLERY_SOURCE_HAIR')=='1'
ACTOR_HAIR_PARENT=os.environ.get('CARNIVAL_GALLERY_ACTOR_HAIR_PARENT')=='1'
HAIR_DIFFUSE=os.environ.get('CARNIVAL_GALLERY_HAIR_DIFFUSE')=='1'
HAIR_MASK_SAMPLERS=os.environ.get('CARNIVAL_GALLERY_HAIR_MASK_SAMPLERS')=='1'
DISABLE_SPECULAR=os.environ.get('CARNIVAL_GALLERY_DISABLE_SPECULAR')=='1'
assert not (SOURCE_HAIR and ACTOR_HAIR_PARENT),'Select one hair parent proof'
FOCUS={n for n in os.environ.get('CARNIVAL_GALLERY_APPEARANCES','').split(',') if n}
assert not (FOLLOW_BODY and DRIVE_OUTFIT),'Pose follower cannot also drive its leader'
BUILD=json.loads((ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930'/FAMILY_DIR/'index.json').read_text())
RELOAD=json.loads((ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930'/FAMILY_DIR/'Reload.json').read_text())
assert BUILD['success'] and RELOAD['success'];assert not (OUT/'index.json').exists(),'Preserve prior evidence'
REPORT={'success':False,'capture_success':False,'errors':[],'captures':[],'visual_review':'pending','assets_saved':False,
 'requested_animation':ANIMATION,'family_directory':FAMILY_DIR,'group':GROUP,'family':FAMILY,
 'drive_outfit_proof':DRIVE_OUTFIT,'actor_hair_parameter_proof':ACTOR_HAIR,
 'outfit_follow_body_proof':FOLLOW_BODY,
 'owned_actor_template':OWNED_ACTOR,
 'source_hair_material_proof':SOURCE_HAIR,'appearance_filter':sorted(FOCUS),
 'actor_hair_parent_proof':ACTOR_HAIR_PARENT,
 'hair_diffuse_only_proof':HAIR_DIFFUSE,
 'linear_mask_sampler_proof':HAIR_MASK_SAMPLERS,
 'specular_show_flag_disabled_proof':DISABLE_SPECULAR,
 'limits':'Selected saved appearances (all unless appearance_filter is specified), common studio lighting, forced actor LOD 0; collection-baked clip frozen at time 1.0 or explicitly empty single-node reference pose. Does not establish live Mass/GPU animation, all LODs, other collections, continuous fit, world lighting or performance.'}
files={r['file']:r['sha256'] for r in BUILD['new_packages']};files.update(BUILD['source_hashes_after'])
if HAIR_MASK_SAMPLERS:
 source_file=Path(r'C:\Program Files\UE_5.8\Engine\Plugins\MetaHuman\MetaHumanCrowd\Content\Materials\M_Hair_Instanced.uasset')
 assert source_file.exists();files[str(source_file)]=hashlib.sha256(source_file.read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in files.items());REPORT['package_hashes_before']=files
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
labels=[]
for row in BUILD['instances']:
 instance=unreal.load_asset(row['candidate']['instance']);assert instance
 if FOCUS and instance.get_name() not in FOCUS:continue
 label='FamilyGallery_'+instance.get_name();labels.append(label)
 actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,label,unreal.Vector(),unreal.Rotator(),OWNED_ACTOR);assert actor and not error,error
 actor.set_actor_hidden_in_game(True)
assert labels and (not FOCUS or len(labels)==len(FOCUS)),'Appearance filter must match exactly'
light=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(150,250,250),unreal.Rotator(pitch=-20,yaw=-120))
lc=light.get_component_by_class(unreal.RectLightComponent);lc.set_mobility(unreal.ComponentMobility.MOVABLE)
for k,v in {'intensity':50,'attenuation_radius':2000,'source_width':400,'source_height':400}.items():lc.set_editor_property(k,v)
fill=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(150,-180,180));fl=fill.get_component_by_class(unreal.PointLightComponent);fl.set_mobility(unreal.ComponentMobility.MOVABLE)
for k,v in {'intensity':20,'attenuation_radius':2000,'cast_shadows':False}.items():fl.set_editor_property(k,v)
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(100,600,110));camera.set_actor_label('FamilyGalleryCamera')
actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(1000,0,200))
SHOTS=[(label,side) for label in labels for side in ('Front','Back')]
S={'phase':'setup','deadline':time.monotonic()+1200,'busy':False,'index':0}

def material_details(mat):
 if not mat:return None
 ml=unreal.MaterialEditingLibrary;row={'path':mat.get_path_name(),'class':mat.get_class().get_name(),'parent_chain':[]}
 parent=mat
 while parent:
  row['parent_chain'].append(parent.get_path_name())
  if isinstance(parent,unreal.Material):break
  parent=parent.get_editor_property('parent')
 if isinstance(mat,unreal.Material):
  row['scalars']={str(n):ml.get_material_default_scalar_parameter_value(mat,n) for n in ml.get_scalar_parameter_names(mat)}
  row['vectors']={str(n):list(ml.get_material_default_vector_parameter_value(mat,n).to_tuple()) for n in ml.get_vector_parameter_names(mat)}
  row['textures']={str(n):(t.get_path_name() if t else None) for n in ml.get_texture_parameter_names(mat) for t in [ml.get_material_default_texture_parameter_value(mat,n)]}
  row['switches']={str(n):ml.get_material_default_static_switch_parameter_value(mat,n) for n in ml.get_static_switch_parameter_names(mat)}
  return row
 if not isinstance(mat,(unreal.MaterialInstanceDynamic,unreal.MaterialInstanceConstant)):return row
 dynamic=isinstance(mat,unreal.MaterialInstanceDynamic)
 row['scalars']={str(n):(mat.get_scalar_parameter_value(n) if dynamic else ml.get_material_instance_scalar_parameter_value(mat,n)) for n in ml.get_scalar_parameter_names(mat)}
 row['vectors']={str(n):list((mat.get_vector_parameter_value(n) if dynamic else ml.get_material_instance_vector_parameter_value(mat,n)).to_tuple()) for n in ml.get_vector_parameter_names(mat)}
 row['textures']={}
 for n in ml.get_texture_parameter_names(mat):
  texture=mat.get_texture_parameter_value(n) if dynamic else ml.get_material_instance_texture_parameter_value(mat,n)
  row['textures'][str(n)]=texture.get_path_name() if texture else None
 static=mat
 while isinstance(static,unreal.MaterialInstanceDynamic):static=static.get_editor_property('parent')
 if isinstance(static,unreal.MaterialInstanceConstant):
  row['switches']={str(n):ml.get_material_instance_static_switch_parameter_value(static,n) for n in ml.get_static_switch_parameter_names(static)}
 return row

def source_groom_details():
 rows=[]
 for name in ('Hair_M_UpdoDutchBraid','Hair_M_UpdoMessyBun'):
  asset_path='/Game/Grooms/'+name+'/'+name+'/'+name
  file=ROOT/'Content'/(asset_path.removeprefix('/Game/')+'.uasset')
  assert file.exists();files[str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
  groom=unreal.load_asset(asset_path);assert isinstance(groom,unreal.GroomAsset),asset_path
  row={'groom':groom.get_path_name(),'cards':[]};rows.append(row)
  for card in groom.get_editor_property('hair_groups_cards'):
   textures=card.get_editor_property('textures');mesh=card.get_editor_property('imported_mesh')
   row['cards'].append({'group':card.get_editor_property('group_index'),'lod':card.get_editor_property('lod_index'),
    'layout':str(textures.get_editor_property('layout')),
    'textures':[t.get_path_name() if t else None for t in textures.get_editor_property('textures')],
    'source_mesh':mesh.get_path_name() if mesh else None,
    'source_materials':[material_details(s.material_interface) for s in mesh.get_editor_property('static_materials')] if mesh else []})
 return rows
def save():REPORT['phase']=S['phase'];(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def finish(error=None):
 if error:REPORT['errors'].append(error)
 REPORT['package_hashes_after']={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files}
 if REPORT['package_hashes_after']!=files:REPORT['errors'].append('A saved candidate or source package changed')
 REPORT['capture_success']=not REPORT['errors'] and len(REPORT['captures'])==len(SHOTS);REPORT['success']=False;save()
 if S.get('pc') and S.get('previous_view'):S['pc'].set_view_target_with_blend(S['previous_view'],0)
 S.clear();S.update(phase='exit',deadline=time.monotonic()+4,busy=True);LE.editor_request_end_play()
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
   S['camera']=next(a for a in allactors if a.get_actor_label()=='FamilyGalleryCamera')
   S['actors']={label:next(a for a in allactors if a.get_actor_label()==label) for label in labels}
   S['pc']=pc;S['previous_view']=pc.get_view_target()
   if pc.get_hud():pc.get_hud().set_editor_property('show_hud',False)
   pawn=unreal.GameplayStatics.get_player_pawn(game,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   cc=S['camera'].camera_component;pp=cc.get_editor_property('post_process_settings')
   for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
    'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_auto_exposure_apply_physical_camera_exposure':True,
    'auto_exposure_apply_physical_camera_exposure':False,'override_bloom_intensity':True,'bloom_intensity':0.}.items():pp.set_editor_property(k,v)
   cc.set_editor_property('post_process_settings',pp);cc.set_editor_property('post_process_blend_weight',1.);cc.set_field_of_view(35.)
   pc.set_view_target_with_blend(S['camera'],0);S['bodies']={};S['hair_expected']={};REPORT['animations']={};REPORT['groom_materials']={};REPORT['groom_parameters_after_proof']={}
   REPORT['source_groom_layouts']=source_groom_details()
   animation=None if ANIMATION=='Reference' else unreal.load_object(None,BUILD['collection']+':AS_'+ANIMATION)
   assert ANIMATION=='Reference' or isinstance(animation,unreal.AnimSequence)
   for label,guest in S['actors'].items():
    comps=guest.get_components_by_class(unreal.SkeletalMeshComponent)
    for comp in comps:comp.set_forced_lod(1)
    body=next(c for c in comps if c.get_name()==('Outfit' if DRIVE_OUTFIT else 'Body'));S['bodies'][label]=body
    assert body.get_editor_property('skeletal_mesh_asset'),'Requested pose driver has no mesh'
    if ANIMATION=='Reference':
     body.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
     body.set_animation(None)
    else:body.play_animation(animation,True)
    if FOLLOW_BODY:
     outfit=next(c for c in comps if c.get_name()=='Outfit')
     assert outfit.get_editor_property('skeletal_mesh_asset'),'Outfit follower has no mesh'
     outfit.set_leader_pose_component(body,True,False)
     assert outfit.get_editor_property('leader_pose_component')==body
    REPORT['animations'][label]=animation.get_path_name() if animation else 'Reference pose (no animation asset)'
    REPORT['groom_materials'][label]=[{'component':c.get_name(),'mesh':c.get_editor_property('skeletal_mesh_asset').get_path_name(),
     'materials':[material_details(c.get_material(i)) for i in range(c.get_num_materials())]}
     for c in comps if 'groom' in c.get_name().lower() and c.get_editor_property('skeletal_mesh_asset')]
    if SOURCE_HAIR:
     for comp in comps:
      if 'groom' not in comp.get_name().lower():continue
      for i in range(comp.get_num_materials()):
       mat=comp.get_material(i)
       if not mat:continue
       textures=material_details(mat).get('textures',{})
       atlas=textures.get('Coverage-Depth-Seed')
       if not atlas:continue
       source_path=atlas.rsplit('/',1)[0]+'/Materials/MI_Hair_Cards'
       source=unreal.load_asset(source_path);assert source,source_path
       file=ROOT/'Content'/(source_path.removeprefix('/Game/')+'.uasset');assert file.exists();files[str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
       comp.set_material(i,source)
       REPORT.setdefault('source_hair_materials',{})[source_path]=material_details(source)
    if ACTOR_HAIR_PARENT or HAIR_MASK_SAMPLERS:
     parent=unreal.load_asset('/MetaHumanCrowd/Materials/MI_Hair_Cards_Actor');assert parent
     S.setdefault('hair_proofs',[])
     for comp in comps:
      if 'groom' not in comp.get_name().lower():continue
      for i in range(comp.get_num_materials()):
       old=comp.get_material(i)
       if not old or not material_details(old).get('textures',{}).get('Coverage-Depth-Seed'):continue
       if HAIR_MASK_SAMPLERS:
        parent,error=unreal.CarnivalCrowdMaterialEditorLibrary.make_compact_hair_sampler_proof(old);assert parent and not error,error
        S['hair_proofs'].append(parent)
        samples=[{'parameter':str(e.get_editor_property('parameter_name')),'sampler':str(e.get_editor_property('sampler_type')),'texture':e.get_editor_property('texture').get_path_name()} for e in unreal.MaterialEditingLibrary.get_material_expressions(parent) if isinstance(e,unreal.MaterialExpressionTextureSampleParameter2D) and str(e.get_editor_property('parameter_name')) in ('Tangent-CoordU','Coverage-Depth-Seed')]
        assert len(samples)==2 and all(s['sampler']==str(unreal.MaterialSamplerType.SAMPLERTYPE_MASKS) for s in samples)
        REPORT.setdefault('mask_sampler_proof_masters',[]).append({'material':parent.get_path_name(),'samples':samples})
       details=material_details(old);clone=unreal.MaterialInstanceConstant();ml=unreal.MaterialEditingLibrary
       ml.set_material_instance_parent(clone,parent)
       for n,v in details.get('scalars',{}).items():ml.set_material_instance_scalar_parameter_value(clone,n,v)
       for n,v in details.get('vectors',{}).items():ml.set_material_instance_vector_parameter_value(clone,n,unreal.LinearColor(*v))
       for n,v in details.get('textures',{}).items():
        if v:ml.set_material_instance_texture_parameter_value(clone,n,unreal.load_object(None,v))
       for n,v in details.get('switches',{}).items():ml.set_material_instance_static_switch_parameter_value(clone,n,v)
       ml.set_material_instance_scalar_parameter_value(clone,'Use PerInstanceCustomData',0.)
       ml.update_material_instance(clone);comp.set_material(i,clone);S['hair_proofs'].append(clone)
       REPORT.setdefault('actor_parent_materials_after_proof',[]).append(material_details(clone))
    if ACTOR_HAIR or HAIR_DIFFUSE:
     for comp in comps:
      if 'groom' not in comp.get_name().lower():continue
      for i in range(comp.get_num_materials()):
       mat=comp.get_material(i)
       if not mat or 'Use PerInstanceCustomData' not in [str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)]:continue
       if not isinstance(mat,unreal.MaterialInstanceDynamic):mat=comp.create_dynamic_material_instance(i)
       assert isinstance(mat,unreal.MaterialInstanceDynamic)
       mat.set_scalar_parameter_value('Use PerInstanceCustomData',0.)
       assert mat.get_scalar_parameter_value('Use PerInstanceCustomData')==0.
       if HAIR_DIFFUSE:
        names={str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)}
        changes={n:0. for n in ('Intensity','RIntensity','TRTIntensity','IntensityFillLight') if n in names}
        for n,v in changes.items():mat.set_scalar_parameter_value(n,v);assert mat.get_scalar_parameter_value(n)==v
        REPORT.setdefault('diffuse_parameter_changes',[]).append({'material':mat.get_path_name(),'scalars':changes})
    REPORT['groom_parameters_after_proof'][label]=[{'component':c.get_name(),'materials':[{'path':m.get_path_name(),'use_per_instance_custom_data':m.get_scalar_parameter_value('Use PerInstanceCustomData')} for i in range(c.get_num_materials()) for m in [c.get_material(i)] if isinstance(m,unreal.MaterialInstanceDynamic) and 'Use PerInstanceCustomData' in [str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(m)]]} for c in comps if 'groom' in c.get_name().lower()]
    S['hair_expected'][label]=[(c,i,c.get_material(i).get_path_name()) for c in comps if 'groom' in c.get_name().lower() and c.get_editor_property('skeletal_mesh_asset') for i in range(c.get_num_materials()) if c.get_material(i)]
   unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0')
   if DISABLE_SPECULAR:
    unreal.SystemLibrary.execute_console_command(game,'ShowFlag.Specular 0')
    REPORT['specular_show_flag']=unreal.SystemLibrary.get_console_variable_int_value('ShowFlag.Specular')
    assert REPORT['specular_show_flag']==0,'Specular show-flag diagnostic did not apply'
   S.update(phase='position',ready=now+20);save();return
  if now<S.get('ready',0):return
  if S['phase']=='position':
   label,side=SHOTS[S['index']]
   for name,guest in S['actors'].items():guest.set_actor_hidden_in_game(name!=label)
   body=S['bodies'][label]
   if ANIMATION!='Reference':body.set_position(1.,False)
   body.set_play_rate(0.)
   focus=unreal.Vector(0,0,115);S['camera'].set_actor_location(focus+unreal.Vector(100,800 if side=='Front' else -800,20),False,True)
   S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(S['camera'].get_actor_location(),focus),True)
   S.update(phase='request',ready=now+5);return
  if S['phase']=='request':
   label,side=SHOTS[S['index']];S['image']=OUT/(label+'_'+side+'.png');S['requested']=time.time()
   unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x800 filename="'+S['image'].as_posix()+'"')
   S.update(phase='capture',ready=now+.5);return
  if S['phase']=='capture':
   file=S['image']
   if not file.exists() or file.stat().st_mtime<S['requested']-1:return
   blob=file.read_bytes();assert blob[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',blob[16:24])==(1280,800)
   label,side=SHOTS[S['index']];body=S['bodies'][label]
   REPORT['captures'].append({'label':label,'side':side,'png':str(file),'animation':REPORT['animations'][label],
    'position':body.get_position(),'camera':list(S['camera'].get_actor_location().to_tuple()),
    'hand_sockets':{n:list(body.get_socket_location(n).to_tuple()) for n in ('hand_l','hand_r')}})
   REPORT['captures'][-1]['body_pose']=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_skeletal_component_pose(body))
   REPORT['captures'][-1]['component_poses']=[]
   REPORT['captures'][-1]['groom_materials_at_capture']=[]
   for comp,i,expected in S['hair_expected'][label]:
    mat=comp.get_material(i);assert mat and mat.get_path_name()==expected,'Hair proof material was replaced before capture'
    details=material_details(mat);REPORT['captures'][-1]['groom_materials_at_capture'].append({'component':comp.get_name(),'slot':i,'material':details})
    if (ACTOR_HAIR or HAIR_DIFFUSE or ACTOR_HAIR_PARENT or HAIR_MASK_SAMPLERS) and 'Use PerInstanceCustomData' in details.get('scalars',{}):
     assert details['scalars']['Use PerInstanceCustomData']==0.,'Hair instanced-data parameter changed before capture'
    if HAIR_DIFFUSE:
     for n in ('Intensity','RIntensity','TRTIntensity','IntensityFillLight'):
      if n in details.get('scalars',{}):assert details['scalars'][n]==0.,'Hair diffuse parameter changed before capture: '+n
   for comp in S['actors'][label].get_components_by_class(unreal.SkeletalMeshComponent):
    if not comp.get_editor_property('skeletal_mesh_asset'):continue
    row={'component':comp.get_name(),'pose':json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_skeletal_component_pose(comp))}
    try:
     leader=comp.get_editor_property('leader_pose_component');row['leader']=leader.get_path_name() if leader else None
    except Exception as e:row['leader_read_error']=str(e)
    row['animation_mode']=str(comp.get_animation_mode());anim=comp.get_anim_instance();row['anim_instance']=anim.get_class().get_name() if anim else None
    REPORT['captures'][-1]['component_poses'].append(row)
   S['index']+=1;save()
   if S['index']==len(SHOTS):finish()
   else:S['phase']='position'
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
handle=unreal.register_slate_post_tick_callback(tick);save();LE.editor_request_begin_play()
