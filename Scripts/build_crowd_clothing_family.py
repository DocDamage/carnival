"""Build one isolated composition without losing authored appearance selections."""
import hashlib,json,os,re,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
GROUP=os.environ['CARNIVAL_FAMILY_GROUP'];FAMILY=os.environ['CARNIVAL_CLOTHING_FAMILY']
CONVERT=os.environ.get('CARNIVAL_CONVERT_BODY_ANIMATIONS')=='1';SUFFIX='Retargeted' if CONVERT else ''
BODY_LOD=int(os.environ.get('CARNIVAL_FAMILY_BODY_SOURCE_LOD','-1'));assert BODY_LOD in (-1,0)
SUFFIX += 'LOD0' if BODY_LOD==0 else ''
assert GROUP in ('G1','G2','G3','G4','G5') and FAMILY in ('Parts','Complete')
BASE=ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930';OUT=BASE/(GROUP+FAMILY+SUFFIX);OUT.mkdir(parents=True,exist_ok=True)
FOLDER='/Game/Carnival/Crowd/ClothingFamilies/'+GROUP+FAMILY+SUFFIX
PACKAGE=FOLDER+'/DA_CarnivalCrowd_'+GROUP+'_'+FAMILY+('_Retargeted' if CONVERT else '')+('_LOD0' if BODY_LOD==0 else '')
ROSTER={'G1':['Dean','Kate','MHC_Advika','Petra'],'G2':['MHC_Hannah','MHC_Kabir','Mason'],
 'G3':['MHC_Crowd84','MHC_Seo','Skye'],'G4':['AmandaBlack','MHC_Natasha'],
 'G5':['Kate','MHC_Natasha','Skotukeda3','Skotukeda4']}[GROUP]
REPORT={'success':False,'errors':[],'phase':'loading','group':GROUP,'family':FAMILY,'convert_body_animations':CONVERT,'instances':[],
 'new_packages':[],'live_config_changed':False,'limits':'Fresh candidate collection and appearance clones. Keeps selected wardrobe keys and parameter overrides; full actor/GPU/LOD, animation, stability and performance acceptance remain required.'}
ML=unreal.MaterialEditingLibrary
REPORT['body_source_lod_diagnostic']=BODY_LOD
def path(o):return o.get_path_name() if o else None
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save():(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def meshstates(prefix):return {path(m):unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(m)
 for m in unreal.ObjectIterator(unreal.SkeletalMesh) if path(m).startswith(prefix)}
def bodylods(collection):
 editor=collection.get_editor_property('Pipeline').get_editor_property('EditorPipeline')
 return {name:[int(row.get_editor_property('SourceLOD')) for row in editor.get_editor_property(name)]
  for name in ('ActorBodyLODs','InstancedBodyLODs')}
def materialstates(prefix):
 result={}
 for m in unreal.ObjectIterator(unreal.MaterialInstanceConstant):
  if not path(m).startswith(prefix):continue
  result[path(m)]={'parent':path(m.get_editor_property('parent')),
   'textures':{str(n):path(ML.get_material_instance_texture_parameter_value(m,n)) for n in ML.get_texture_parameter_names(m)},
   'scalars':{str(n):ML.get_material_instance_scalar_parameter_value(m,n) for n in ML.get_scalar_parameter_names(m)},
   'vectors':{str(n):list(ML.get_material_instance_vector_parameter_value(m,n).to_tuple()) for n in ML.get_vector_parameter_names(m)},
   'switches':{str(n):ML.get_material_instance_static_switch_parameter_value(m,n) for n in ML.get_static_switch_parameter_names(m)}}
 return result
save()
try:
 if CONVERT:
  agreement=json.loads((ROOT/'Saved/CharacterRepairs/DeanConvertedAnimationNeutralReference_20260930/index.json').read_text())
  assert agreement['success'] and not agreement['errors'],'Complete-clip pose agreement must pass before saving a retargeted family'
 assert not (ROOT/'Content'/(PACKAGE.removeprefix('/Game/')+'.uasset')).exists(),'Refuse to overwrite candidate evidence'
 survey=json.loads((BASE/'SourceRoster.json').read_text());assert survey['success'] and not survey['errors']
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
 source=unreal.load_asset('/Game/Carnival/Crowd/Collections/DA_CarnivalCrowd_'+GROUP+'_FINAL2');assert source
 selected=[r for r in survey['instances'] if r['collection']==path(source) and r['family']==FAMILY];assert selected
 source_files=[ROOT/'Content'/(path(source).split('.')[0].removeprefix('/Game/')+'.uasset')]
 source_files += [ROOT/'Content'/(r['instance'].split('.')[0].removeprefix('/Game/')+'.uasset') for r in selected]
 if CONVERT:
  source_files += [ROOT/'Content'/p for p in ('Carnival/Crowd/DA_CarnivalCrowdAnimations.uasset',
   'Town/Demo/Characters/Mannequins/Animations/Manny/MM_Idle.uasset',
   'Town/Demo/Characters/Mannequins/Animations/Manny/MM_Walk_InPlace.uasset',
   'Town/Demo/Characters/Mannequins/Meshes/SK_Mannequin.uasset')]
 for name in ROSTER:
  character_path='/Game/Carnival/MetaHumans/Dean' if name=='Dean' else json.loads((ROOT/'Saved/CharacterRepairs/CrowdHeadSkinBakes_20260930'/name/'index.json').read_text())['source']
  source_files.append(ROOT/'Content'/(character_path.removeprefix('/Game/')+'.uasset'))
 REPORT['source_hashes_before']={str(p):digest(p) for p in source_files}
 for p,h in REPORT['source_hashes_before'].items():
  if p in survey['hashes']:assert h==survey['hashes'][p],'Source changed after roster survey'
 prefix=path(source)+':';REPORT['source_meshes_before']=meshstates(prefix);REPORT['source_materials_before']=materialstates(prefix)
 REPORT['source_slots']=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_collection_slots(source))
 REPORT['source_body_lods_before']=bodylods(source)
 REPORT['phase']='building';save()
 candidate,error=unreal.CarnivalCrowdMaterialEditorLibrary.build_clothing_family_collection(source,PACKAGE,FAMILY=='Complete',CONVERT,BODY_LOD);assert candidate and not error,error
 REPORT['candidate_slots']=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_collection_slots(candidate))
 REPORT['candidate_body_lods']=bodylods(candidate)
 if BODY_LOD==0:assert all(lods==[0] for lods in REPORT['candidate_body_lods'].values())
 expected={r['slot']:r['direct_item_count'] for r in REPORT['source_slots']['slots']}
 for r in REPORT['candidate_slots']['slots']:
  excluded=(r['slot']=='Outfits' and FAMILY=='Parts') or (r['slot'] in ('Top Garment','Bottom Garment','Shoes') and FAMILY=='Complete')
  assert r['direct_item_count']==(0 if excluded else expected[r['slot']]),r
 REPORT['phase']='binding_reviewed_heads';save();textures={}
 for name in ROSTER:
  proof_dir=ROOT/'Saved/CharacterRepairs'/('DeanSkinSavedProof_20260930' if name=='Dean' else 'CrowdHeadSkinBakes_20260930/'+name)
  proof=json.loads((proof_dir/'index.json').read_text());reload=json.loads((proof_dir/'Reload.json').read_text())
  assert proof['success'] and reload['success']
  rows=proof['assets_saved'] if name=='Dean' else proof['saved_textures'];textures[name]={}
  for row in rows:
   assert digest(row['file'])==row['sha256'];textures[name][row['parameter']]=unreal.load_asset(row['asset']);assert textures[name][row['parameter']]
 counts={name:0 for name in ROSTER};REPORT['head_bindings']=[]
 for m in list(unreal.ObjectIterator(unreal.MaterialInstanceConstant)):
  if not path(m).startswith(path(candidate)+':'):continue
  match=re.fullmatch(r'MI_Face(?:Combo)?_(.+)_head_LOD.+',m.get_name())
  if not match:continue
  name=match[1];assert name in textures,name
  for parameter,texture in textures[name].items():
   ML.set_material_instance_texture_parameter_value(m,parameter,texture)
   assert ML.get_material_instance_texture_parameter_value(m,parameter)==texture
  ML.set_material_instance_static_switch_parameter_value(m,'Use Baked Material',True)
  assert ML.get_material_instance_static_switch_parameter_value(m,'Use Baked Material');ML.update_material_instance(m)
  counts[name]+=1;REPORT['head_bindings'].append({'material':path(m),'head':name,'textures':{n:path(t) for n,t in textures[name].items()}})
 assert all(c>=4 for c in counts.values()),counts;REPORT['head_counts']=counts
 REPORT['phase']='cloning_selected_appearances';save();objects=[candidate]
 for row in selected:
  original=unreal.load_asset(row['instance']);assert original
  before=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_instance_selections(original))
  assert before['selections']==row['selections'] and before['parameter_overrides_sha1']==row['parameter_overrides_sha1']
  target=FOLDER+'/Instances/'+original.get_name()
  clone,error=unreal.CarnivalCrowdMaterialEditorLibrary.clone_instance_for_clothing_family(original,candidate,target);assert clone and not error,error
  after=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_instance_selections(clone))
  for key in ('selections','parameter_overrides_sha1','parameter_overrides_text_length'):assert before[key]==after[key],key
  actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(clone,'Family_'+original.get_name(),unreal.Vector(),unreal.Rotator());assert actor and not error,error
  components=[]
  for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
   mesh=comp.get_editor_property('skeletal_mesh_asset')
   if mesh:components.append({'name':comp.get_name(),'initial_visibility':comp.is_visible(),
    'materials':[path(comp.get_material(i)) for i in range(comp.get_num_materials())],
    'geometry':json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_loaded_mesh_sections(mesh))})
  assert any(c['name'].startswith('Outfit') for c in components),'Selected appearance has no clothing component'
  if BODY_LOD==0:
   expected_clothes=sum(not r['empty'] for r in after['selections'] if r['slot'] in ('Outfits','Top Garment','Bottom Garment','Shoes'))
   assert sum(c['name'].startswith('Outfit') for c in components)==expected_clothes,'A selected garment is missing from the LOD0 diagnostic assembly'
  REPORT['instances'].append({'source':before,'candidate':after,'components':components});objects.append(clone)
 REPORT['source_meshes_after']=meshstates(prefix);REPORT['source_materials_after']=materialstates(prefix)
 REPORT['source_body_lods_after']=bodylods(source)
 assert REPORT['source_body_lods_after']==REPORT['source_body_lods_before'],'Source body LOD settings changed'
 assert REPORT['source_meshes_after']==REPORT['source_meshes_before'],'Source loaded mesh structure changed'
 assert REPORT['source_materials_after']==REPORT['source_materials_before'],'Source loaded materials changed'
 REPORT['phase']='saving_new_candidates';save()
 for obj in objects:
  assert path(obj).startswith(FOLDER+'/');assert unreal.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False)
  file=ROOT/'Content'/(path(obj).split('.')[0].removeprefix('/Game/')+'.uasset')
  REPORT['new_packages'].append({'asset':path(obj),'file':str(file),'sha256':digest(file)});save()
 REPORT['source_hashes_after']={str(p):digest(p) for p in source_files}
 assert REPORT['source_hashes_after']==REPORT['source_hashes_before']
 REPORT.update(success=True,phase='complete',collection=path(candidate))
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:save()
