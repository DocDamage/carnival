"""Reload saved isolated collections and inspect their actual selected assemblies."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/DeanBodyOwnershipBuild_20260930';OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'assets_saved':False,'proofs':[],
 'limits':'Fresh-process package, binding and assembled geometry verification. Rendered appearance, GPU representation and live crowd acceptance remain separate.'}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def path(o):return o.get_path_name() if o else None
try:
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
 for kind in ('Mixed','Parts'):
  build=json.loads((OUT/kind/'index.json').read_text());assert build['success'] and not build['errors']
  hashes={row['file']:row['sha256'] for row in build['new_packages']}
  hashes.update(build['source_hashes_before']);assert all(digest(p)==h for p,h in hashes.items())
  collection=unreal.load_asset(build['collection']);instance=unreal.load_asset(build['instance']);assert collection and instance
  actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'Reload'+kind,unreal.Vector(),unreal.Rotator());assert actor and not error,error
  row={'kind':kind,'collection':path(collection),'instance':path(instance),
   'slots':json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_collection_slots(collection)),'components':[],
   'verified_package_hashes':hashes}
  for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
   mesh=comp.get_editor_property('skeletal_mesh_asset')
   if mesh:row['components'].append({'name':comp.get_name(),'initial_visibility':comp.is_visible(),
    'materials':[path(comp.get_material(i)) for i in range(comp.get_num_materials())],
    'geometry':json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_loaded_mesh_sections(mesh))})
  assert {c['name'] for c in row['components']} >= {'Body','Face','Outfit','Outfit2','Outfit3'}
  skin=json.loads((ROOT/'Saved/CharacterRepairs/DeanSkinSavedProof_20260930/index.json').read_text())
  expected={t['parameter']:t['asset'] for t in skin['assets_saved']}
  targets=[]
  for mat in unreal.ObjectIterator(unreal.MaterialInstanceConstant):
   if not path(mat).startswith(path(collection)+':') or not mat.get_name().startswith(('MI_Face_Dean_','MI_FaceCombo_Dean_')):continue
   textures={n:path(unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mat,n))
    for n in expected}
   targets.append({'material':path(mat),'textures':textures})
  row['head_materials']=targets;assert targets
  for mat in targets:
   for name,asset in expected.items():
    texture=unreal.load_asset(asset);assert texture
    obj=unreal.load_object(None,mat['material']);assert obj
    assert unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(obj,name)==texture
  assert all(digest(p)==h for p,h in hashes.items());REPORT['proofs'].append(row)
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'Reload.json').write_text(json.dumps(REPORT,indent=2))
