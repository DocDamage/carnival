"""Plan canonical crewneck hard-reference closure from the asset registry."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterRepairs'
PREFIX='/Game/Fab/MetaHuman/OA_Crewneckt/'
SOURCE='/Game/Carnival/MetaHumans/Additional/Amanda/AmandaBlack/'
REPORT={'success':False,'packages':[],'missing_sources':[],'errors':[],
        'limits':'Read-only transitive asset-registry plan; no source or destination changes.'}
try:
 seeds=json.loads((OUT/'CrowdLiveMissingDependencies_20260930.json').read_text())
 queue=sorted({r['missing'] for r in seeds['missing_dependencies']});seen=set()
 registry=unreal.AssetRegistryHelpers.get_asset_registry()
 options=unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,
     include_soft_package_references=True,include_searchable_names=False,
     include_hard_management_references=False,include_soft_management_references=False)
 while queue:
  package=queue.pop(0)
  if package in seen:continue
  seen.add(package);assert package.startswith(PREFIX),package
  source_package=SOURCE+package.removeprefix('/Game/')
  source=ROOT/'Content'/(source_package.removeprefix('/Game/')+'.uasset')
  if not source.exists():REPORT['missing_sources'].append({'package':package,'source':str(source)});continue
  dependencies=sorted(str(p) for p in registry.get_dependencies(source_package,options))
  queue.extend(p for p in dependencies if p.startswith(PREFIX) and p not in seen)
  REPORT['packages'].append({'package':package,'source_package':source_package,
      'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'dependencies':dependencies})
 assert REPORT['packages'] and not REPORT['missing_sources'],REPORT['missing_sources']
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc())
(OUT/'AmandaClothingDependencyClosurePlan_20260930.json').write_text(json.dumps(REPORT,indent=2))
