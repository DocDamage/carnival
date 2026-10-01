"""Read the live appearance roster and its selected clothing compositions."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();OUT=ROOT/'Saved/CharacterRepairs/CrowdClothingFamilies_20260930';OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'assets_saved':False,'instances':[],'hashes':{},'limits':'Source roster and selected keys only; candidate assemblies and visual behavior require validation.'}
def path(o):return o.get_path_name() if o else None
def record(o):
 p=path(o).split('.')[0];file=ROOT/'Content'/(p.removeprefix('/Game/')+'.uasset')
 if str(file) not in REPORT['hashes']:REPORT['hashes'][str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
try:
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
 config=unreal.load_asset('/Game/Carnival/Crowd/Mass/DA_CarnivalCrowdEntityConfig');assert config;record(config)
 traits=config.get_editor_property('config').get_editor_property('traits')
 visual=next(t for t in traits if unreal.Object.get_class(t).get_name()=='MetaHumanMassCrowdVisualizationTrait')
 instances=list(visual.get_editor_property('character_instances'));assert len(instances)==32
 for instance in instances:
  assert path(instance).startswith('/Game/Carnival/Crowd/Instances/ExpandedFinal2/');record(instance)
  collection=instance.get_meta_human_collection();assert collection;record(collection)
  row=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_instance_selections(instance));assert row.get('selections')
  slots={s['slot'] for s in row['selections'] if not s['empty']};assert all(s['root'] for s in row['selections'])
  complete='Outfits' in slots;parts=bool(slots & {'Top Garment','Bottom Garment','Shoes'})
  assert not (complete and parts),(path(instance),slots)
  row['family']='Complete' if complete else 'Parts' if parts else 'Default'
  if row['family']=='Default':
   assert 'G6_FINAL2' in row['collection'],'Inspect unspecified clothing in a mixed collection before assigning a family'
  REPORT['instances'].append(row)
 assert len({r['instance'] for r in REPORT['instances']})==32
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in REPORT['hashes'].items())
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'SourceRoster.json').write_text(json.dumps(REPORT,indent=2))
