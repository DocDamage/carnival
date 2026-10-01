"""Verify one saved composition in a fresh editor process."""
import hashlib,json,os,re,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();GROUP=os.environ['CARNIVAL_FAMILY_GROUP'];FAMILY=os.environ['CARNIVAL_CLOTHING_FAMILY']
CONVERT=os.environ.get('CARNIVAL_CONVERT_BODY_ANIMATIONS')=='1'
BODY_LOD=int(os.environ.get('CARNIVAL_FAMILY_BODY_SOURCE_LOD','-1'));assert BODY_LOD in (-1,0)
OUT=ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930'/(GROUP+FAMILY+('Retargeted' if CONVERT else '')+('LOD0' if BODY_LOD==0 else ''))
REPORT={'success':False,'errors':[],'assets_saved':False,'instances':[],
 'animation_agreements':[],'metadata_agreements':[],'position_tolerance_cm':.1,'rotation_tolerance_degrees':.1,
 'limits':'Fresh-process hashes, selection and authored-override fingerprints, head bindings and assembled mesh geometry. Converted families also check shared and selected-head clips over 65 times on every body/outfit bone, against source playback with unanimated bones restored to mesh reference. Appearance/GPU/LOD/continuous-animation/stability/performance acceptance are separate.'}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def path(o):return o.get_path_name() if o else None
def differences(a,b,key=''):
 if type(a)!=type(b):return [{'field':key,'before':a,'after':b}]
 if isinstance(a,dict):
  return [d for k in sorted(set(a)|set(b)) for d in differences(a.get(k),b.get(k),key+'/'+str(k))]
 if isinstance(a,list):
  if len(a)!=len(b):return [{'field':key+'/length','before':len(a),'after':len(b)}]
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in differences(x,y,key+'/'+str(i))]
 return [] if a==b else [{'field':key,'before':a,'after':b}]
try:
 build=json.loads((OUT/'index.json').read_text());assert build['success'] and not build['errors']
 assert all(digest(p)==h for p,h in build['source_hashes_after'].items())
 for row in build['new_packages']:assert digest(row['file'])==row['sha256']
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
 collection=unreal.load_asset(build['collection']);assert collection
 if CONVERT:
  original_collection=build['instances'][0]['source']['collection']
  REPORT['metadata_reference_collection']=original_collection
  heads=sorted({row['head'] for row in build['head_bindings']})
  def metadata(clip):
   return {'duration':clip.get_play_length(),'rate_scale':clip.get_editor_property('rate_scale'),
    'notify_count':len(unreal.AnimationLibrary.get_animation_notify_events(clip)),
    'markers':[{'name':str(m.marker_name),'time':m.time} for m in unreal.AnimationLibrary.get_animation_sync_markers(clip)]}
  for animation in ('Idle','Walk'):
   for name in ['AS_'+animation]+['AS_'+h+'_'+animation+'_Baked' for h in heads]:
    before=unreal.load_object(None,original_collection+':'+name);after=unreal.load_object(None,path(collection)+':'+name);assert before and after
    a,b=metadata(before),metadata(after);REPORT['metadata_agreements'].append({'clip':name,'before':a,'after':b,'equal':a==b})
   input_clip=unreal.load_object(None,path(collection)+':AS_Input_'+animation);shared=unreal.load_object(None,path(collection)+':AS_'+animation);assert input_clip and shared
   a,b=metadata(shared),metadata(input_clip);REPORT['metadata_agreements'].append({'clip':'AS_Input_'+animation,'before':a,'after':b,'equal':a==b})
  assert all(r['equal'] for r in REPORT['metadata_agreements']),'Playback metadata changed'
 for row in build['head_bindings']:
  mat=unreal.load_object(None,row['material']);assert mat
  for name,asset in row['textures'].items():assert unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mat,name)==unreal.load_asset(asset)
  assert unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(mat,'Use Baked Material')
 for row in build['instances']:
  candidate=unreal.load_asset(row['candidate']['instance']);assert candidate
  selections=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_instance_selections(candidate))
  assert selections==row['candidate'],'Saved selections or parameter overrides changed'
  actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(candidate,'Reload_'+candidate.get_name(),unreal.Vector(),unreal.Rotator());assert actor and not error,error
  components=[]
  for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
   mesh=comp.get_editor_property('skeletal_mesh_asset')
   if mesh:components.append({'name':comp.get_name(),'initial_visibility':comp.is_visible(),
    'materials':[path(comp.get_material(i)) for i in range(comp.get_num_materials())],
    'geometry':json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_loaded_mesh_sections(mesh))})
  diff=differences(row['components'],components)
  normalizations=[];unexpected=[]
  for d in diff:
   match=re.fullmatch(r'/(\d+)/geometry/materials/(\d+)/imported_slot',d['field'])
   if match:
    ci,mi=map(int,match.groups());before_materials=row['components'][ci]['geometry']['materials']
    # SkeletalMesh::PostLoad calls MeshUtilities::FixupMaterialSlotNames.
    # Reproduce its exact fill-and-unique rule; never normalize material paths,
    # section bindings, geometry or arbitrary nonempty names.
    used=set();expected=[]
    for material in before_materials:
     base=material['imported_slot'] if material['imported_slot']!='None' else material['slot']
     name=base;number=1
     while name.casefold() in used:name=base+'_'+str(number);number+=1
     used.add(name.casefold());expected.append(name)
    if d['after']==expected[mi]:normalizations.append(dict(d,reason='Engine PostLoad fills missing names and disambiguates duplicate imported names'));continue
   unexpected.append(d)
  REPORT['instances'].append({'instance':path(candidate),'selections':selections,'components':components,
   'component_differences':diff,'imported_slot_name_fills':normalizations,'unexpected_differences':unexpected})
  assert not unexpected,'Saved assembly geometry or material paths changed beyond filling empty imported slot names'
  if CONVERT:
   head_key=next(s['key'] for s in selections['selections'] if s['slot']=='Head')
   head_match=re.search(r'Asset=([^,]+)',head_key);assert head_match,head_key
   head_name=head_match[1].rsplit('.',1)[-1]
   pose_components=[c for c in actor.get_components_by_class(unreal.SkeletalMeshComponent)
    if c.get_name()=='Body' or c.get_name().startswith('Outfit')]
   body=next(c for c in pose_components if c.get_name()=='Body')
   assert body.get_editor_property('skeletal_mesh_asset'),'Assembled appearance has no body pose driver'
   REPORT['instances'][-1]['unused_outfit_components']=[c.get_name() for c in pose_components
    if c.get_name().startswith('Outfit') and not c.get_editor_property('skeletal_mesh_asset')]
   body_meshes=[c.get_editor_property('skeletal_mesh_asset') for c in pose_components if c.get_editor_property('skeletal_mesh_asset')]
   assert len(body_meshes)>=2,'Assembled appearance has no clothing mesh'
   for animation,source_name in (('Idle','MM_Idle'),('Walk','MM_Walk_InPlace')):
    source=unreal.load_asset('/Game/Town/Demo/Characters/Mannequins/Animations/Manny/'+source_name);assert source
    for clip_name in ('AS_'+animation,'AS_'+head_name+'_'+animation+'_Baked'):
     clip=unreal.load_object(None,path(collection)+':'+clip_name);assert isinstance(clip,unreal.AnimSequence),clip_name
     for mesh in body_meshes:
      agreement,error=unreal.CarnivalCrowdMaterialEditorLibrary.describe_animation_pose_agreement(mesh,source,clip,65,normalize_unanimated_source_bones=True);assert not error,error
      REPORT['animation_agreements'].append({'instance':path(candidate),'clip':clip_name,'agreement':json.loads(agreement)})
   (OUT/'Reload.json').write_text(json.dumps(REPORT,indent=2))
 if CONVERT:
  violations=[r for r in REPORT['animation_agreements'] if r['agreement']['maximum_bone_position_error_cm']>REPORT['position_tolerance_cm']
   or r['agreement']['maximum_bone_rotation_error_degrees']>REPORT['rotation_tolerance_degrees']]
  assert not violations,'Saved animation agreement failed on '+str(len(violations))+' comparisons'
 assert all(digest(p)==h for p,h in build['source_hashes_after'].items())
 for row in build['new_packages']:assert digest(row['file'])==row['sha256']
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'Reload.json').write_text(json.dumps(REPORT,indent=2))
