"""Compare original/candidate poses and shadow response without saving assets."""
import hashlib,json,os,struct,time,traceback
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()).resolve();OUT=ROOT/'Saved/CharacterRepairs/DeanFamilyPoseAndShadow_20260930';OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'index.json').exists(),'Preserve previous pose evidence'
REPORT={'success':False,'capture_success':False,'errors':[],'captures':[],'visual_review':'pending','assets_saved':False,
 'limits':'Matched actual original/candidate Dean actors, reference/direct/own/cross-baked idle, tick-policy and no-shadow comparisons. Studio forced actor LOD 0, fixed time 1.0, wider fixed camera. No live crowd/GPU/all-character/continuous-animation/performance acceptance.'}
PATHS={'Original':'/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean',
 'Candidate':'/Game/Carnival/Crowd/ClothingFamilies/G1Parts/Instances/MHI_Dean'}
PACKAGES=['/Game/Carnival/Crowd/Collections/DA_CarnivalCrowd_G1_FINAL2',
 '/Game/Carnival/Crowd/ClothingFamilies/G1Parts/DA_CarnivalCrowd_G1_Parts',*PATHS.values()]
files=[ROOT/'Content'/(p.removeprefix('/Game/')+'.uasset') for p in PACKAGES]
REPORT['package_hashes_before']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
collections={}
for name,path in PATHS.items():
 instance=unreal.load_asset(path);assert instance;collections[name]=instance.get_meta_human_collection().get_path_name()
 actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'Pose'+name,unreal.Vector(),unreal.Rotator());assert actor and not error,error
 actor.set_actor_hidden_in_game(True)
light=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(150,250,250),unreal.Rotator(pitch=-20,yaw=-120));light.set_actor_label('PoseKeyLight')
lc=light.get_component_by_class(unreal.RectLightComponent);lc.set_mobility(unreal.ComponentMobility.MOVABLE)
for k,v in {'intensity':50,'attenuation_radius':2000,'source_width':400,'source_height':400}.items():lc.set_editor_property(k,v)
fill=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(150,-180,180));fl=fill.get_component_by_class(unreal.PointLightComponent);fl.set_mobility(unreal.ComponentMobility.MOVABLE)
for k,v in {'intensity':20,'attenuation_radius':2000,'cast_shadows':False}.items():fl.set_editor_property(k,v)
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(100,800,135));camera.set_actor_label('PoseCamera')
actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(1000,0,200))
CASES=[(name,'Reference','Always',True) for name in PATHS]+[(name,'Direct','Always',True) for name in PATHS]
CASES += [(name,name,policy,True) for policy in ('Default','Always') for name in PATHS]
CASES += [('Original','Candidate','Always',True),('Candidate','Original','Always',True),('Candidate','Candidate','Always',False)]
SHOTS=[(case,side) for case in CASES for side in ('Front','Back')]
S={'phase':'setup','deadline':time.monotonic()+1800,'busy':False,'index':0}
def save():REPORT['phase']=S['phase'];(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def path(o):return o.get_path_name() if o else None
def prop(o,n):
 try:return o.get_editor_property(n)
 except Exception:return None
def shader(mat):
 root=mat
 while isinstance(root,unreal.MaterialInstance):root=root.get_editor_property('parent')
 ml=unreal.MaterialEditingLibrary
 def tex(n):return mat.get_texture_parameter_value(n) if isinstance(mat,unreal.MaterialInstanceDynamic) else ml.get_material_instance_texture_parameter_value(mat,n)
 def scalar(n):return mat.get_scalar_parameter_value(n) if isinstance(mat,unreal.MaterialInstanceDynamic) else ml.get_material_instance_scalar_parameter_value(mat,n)
 row={'material':path(mat),'root':path(root),'blend_mode':str(prop(root,'blend_mode')),
  'tangent_space_normal':prop(root,'tangent_space_normal'),
  'scalars':{str(n):scalar(n) for n in ml.get_scalar_parameter_names(mat)},
  'textures':{str(n):path(tex(n)) for n in ml.get_texture_parameter_names(mat)},'expressions':[]}
 if isinstance(root,unreal.Material):
  for expr in ml.get_material_expressions(root):
   row['expressions'].append({'class':unreal.Object.get_class(expr).get_name(),'parameter':str(prop(expr,'parameter_name')),
    'texture':path(prop(expr,'texture')),'function':path(prop(expr,'material_function'))})
 return row
def finish(error=None):
 if error:REPORT['errors'].append(error)
 REPORT['package_hashes_after']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 if REPORT['package_hashes_after']!=REPORT['package_hashes_before']:REPORT['errors'].append('A reference/candidate package changed')
 REPORT['capture_success']=not REPORT['errors'] and len(REPORT['captures'])==len(SHOTS);REPORT['success']=REPORT['capture_success'];save()
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
   S['actors']={name:next(a for a in allactors if a.get_actor_label()=='Pose'+name) for name in PATHS}
   S['camera']=next(a for a in allactors if a.get_actor_label()=='PoseCamera');S['key']=next(a for a in allactors if a.get_actor_label()=='PoseKeyLight').get_component_by_class(unreal.RectLightComponent)
   S['pc']=pc;S['previous_view']=pc.get_view_target()
   if pc.get_hud():pc.get_hud().set_editor_property('show_hud',False)
   pawn=unreal.GameplayStatics.get_player_pawn(game,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   cc=S['camera'].camera_component;pp=cc.get_editor_property('post_process_settings')
   for k,v in {'override_auto_exposure_method':True,'auto_exposure_method':unreal.AutoExposureMethod.AEM_MANUAL,
    'override_auto_exposure_bias':True,'auto_exposure_bias':0.,'override_auto_exposure_apply_physical_camera_exposure':True,
    'auto_exposure_apply_physical_camera_exposure':False,'override_bloom_intensity':True,'bloom_intensity':0.}.items():pp.set_editor_property(k,v)
   cc.set_editor_property('post_process_settings',pp);cc.set_editor_property('post_process_blend_weight',1.);cc.set_field_of_view(35.)
   pc.set_view_target_with_blend(S['camera'],0);S['bodies']={};S['defaults']={};S['shadow_defaults']=[];REPORT['shader_inputs']={};REPORT['initial_poses']={}
   for name,guest in S['actors'].items():
    comps=guest.get_components_by_class(unreal.SkeletalMeshComponent)
    for comp in comps:comp.set_forced_lod(1)
    body=next(c for c in comps if c.get_name()=='Body');S['bodies'][name]=body
    S['defaults'][name]=body.get_editor_property('visibility_based_anim_tick_option')
    REPORT['initial_poses'][name]=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_skeletal_component_pose(body))
    REPORT['shader_inputs'][name]=[]
    for comp in guest.get_components_by_class(unreal.MeshComponent):
     S['shadow_defaults'].append((comp,comp.get_editor_property('cast_shadow')))
     if comp.get_name().startswith('Outfit'):
      for i in range(comp.get_num_materials()):REPORT['shader_inputs'][name].append(shader(comp.get_material(i)))
   S['clips']={name:unreal.load_object(None,p+':AS_Idle') for name,p in collections.items()};assert all(S['clips'].values())
   S['clips']['Direct']=unreal.load_asset('/Game/Town/Demo/Characters/Mannequins/Animations/Manny/MM_Idle');assert S['clips']['Direct']
   unreal.SystemLibrary.execute_console_command(game,'t.IdleWhenNotForeground 0');S.update(phase='position',ready=now+20);save();return
  if now<S.get('ready',0):return
  if S['phase']=='position':
   (name,clip,policy,shadows),side=SHOTS[S['index']]
   for label,guest in S['actors'].items():guest.set_actor_hidden_in_game(label!=name)
   body=S['bodies'][name]
   body.set_editor_property('visibility_based_anim_tick_option',S['defaults'][name] if policy=='Default' else unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
   body.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
   if clip=='Reference':body.set_animation(None)
   else:body.play_animation(S['clips'][clip],True);body.set_position(1.,False);body.set_play_rate(0.)
   S['key'].set_editor_property('cast_shadows',shadows)
   for comp,default in S['shadow_defaults']:comp.set_cast_shadow(default if shadows else False)
   focus=unreal.Vector(0,0,115);S['camera'].set_actor_location(focus+unreal.Vector(100,800 if side=='Front' else -800,20),False,True)
   S['camera'].set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(S['camera'].get_actor_location(),focus),True)
   S.update(phase='request',ready=now+5);return
  if S['phase']=='request':
   (name,clip,policy,shadows),side=SHOTS[S['index']];S['label']='_'.join((name,clip,policy,'Shadow' if shadows else 'NoShadow',side))
   S['image']=OUT/(S['label']+'.png');S['requested']=time.time()
   unreal.SystemLibrary.execute_console_command(game,'HighResShot 1280x800 filename="'+S['image'].as_posix()+'"');S.update(phase='capture',ready=now+.5);return
  if S['phase']=='capture':
   file=S['image']
   if not file.exists() or file.stat().st_mtime<S['requested']-1:return
   data=file.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',data[16:24])==(1280,800)
   (name,clip,policy,shadows),side=SHOTS[S['index']]
   REPORT['captures'].append({'label':S['label'],'actor':name,'requested_clip':clip,'tick_policy':policy,'shadows':shadows,'side':side,'png':str(file),
    'body':json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_skeletal_component_pose(S['bodies'][name]))})
   S['index']+=1;save()
   if S['index']==len(SHOTS):finish()
   else:S['phase']='position'
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
handle=unreal.register_slate_post_tick_callback(tick);save();LE.editor_request_begin_play()
