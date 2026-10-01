"""Read selected G2 wardrobe sources and body compatibility; never save assets."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();OUT=ROOT/'Saved/CharacterRepairs/G2SelectedClothingSource_20260930'
OUT.mkdir(parents=True,exist_ok=False)
REPORT={'success':False,'errors':[],'assets_saved':False,'wardrobe':[],'instances':[]}
def path(o):return o.get_path_name() if o else None
def assetfile(o):return ROOT/'Content'/(path(o).split('.')[0].removeprefix('/Game/')+'.uasset')
try:
 collection=unreal.load_asset('/Game/Carnival/Crowd/Collections/DA_CarnivalCrowd_G2_FINAL2');assert collection
 sourcefile=assetfile(collection);before=hashlib.sha256(sourcefile.read_bytes()).hexdigest()
 for item in list(unreal.ObjectIterator(unreal.MetaHumanWardrobeItem)):
  if not path(item).startswith(path(collection)+':'):continue
  reference=item.get_editor_property('PrincipalAsset').get_editor_property('Asset')
  source=reference if isinstance(reference,unreal.Object) else unreal.load_asset(str(reference))
  if not source or source.get_class().get_name() not in ('ChaosOutfitAsset','SkeletalMesh'):continue
  pipeline=item.get_editor_property('Pipeline')
  editor=pipeline.get_editor_property('EditorPipeline') if pipeline else None
  row={'item':path(item),'source':path(source),'source_class':source.get_class().get_name(),
   'pipeline':path(pipeline),'editor':path(editor)}
  if editor:
   try:row['compatible_bodies']=[path(x) if isinstance(x,unreal.Object) else str(x) for x in editor.get_editor_property('CompatibleBodies')]
   except Exception:row['compatible_bodies']='Not exposed by this pipeline'
  if isinstance(source,unreal.SkeletalMesh):row['geometry']=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_loaded_mesh_sections(source))
  file=assetfile(source);row['source_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();REPORT['wardrobe'].append(row)
 for name in ('MHI_MHC_Kabir','MHI_Alt05_MHC_Kabir'):
  instance=unreal.load_asset('/Game/Carnival/Crowd/Instances/ExpandedFinal2/'+name);assert instance
  actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'Source_'+name,unreal.Vector(),unreal.Rotator(),True);assert actor and not error,error
  REPORT['instances'].append({'instance':path(instance),'components':[
   {'name':c.get_name(),'mesh':path(c.get_editor_property('skeletal_mesh_asset')),'materials':[path(c.get_material(i)) for i in range(c.get_num_materials())]}
   for c in actor.get_components_by_class(unreal.SkeletalMeshComponent)]})
 REPORT['collection_sha256_before']=before
 REPORT['collection_sha256_after']=hashlib.sha256(sourcefile.read_bytes()).hexdigest();assert REPORT['collection_sha256_after']==before
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
