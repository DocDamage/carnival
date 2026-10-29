"""Clear only surveyed spruce roots obstructing prison/East Dock wayfinding.

Use foliage-owned removal and the established orphan-component fix. Back up each
seasonal level before and after; reload and prove every selected root is absent.
"""
import hashlib,json,re,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion/WayfindingSpruceClearance_20261029';OUT.mkdir(parents=True,exist_ok=False)
BACKUP=Path(r'D:\CarnivalBackups\wayfinding_spruces_20261029');BACKUP.mkdir(parents=True,exist_ok=False)
MAIN=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
CONNECT=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
NAMES=('Lv_LightingDay','Lv_LightingNight','Lv_LightingNightSnow')
R={'success':False,'errors':[],'levels':{}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def components(actors):
 return [a for a in actors if a.get_class().get_name()=='InstancedFoliageActor']
def descriptions(actors,lo,hi):
 return [(a,str(s)) for a in components(actors) for s in unreal.CarnivalRouteEditorLibrary.describe_foliage_in_box(a,lo,hi)]
def left(actors,lo,hi):
 return sum(int(re.search(r'inside=(\d+)',s).group(1)) for a,s in descriptions(actors,lo,hi) if s.startswith('component') and 'Spruce' in s)
try:
 source=json.loads((ROOT/'Saved/WorldExpansion/WayfindingFoliage_20261029_v2.json').read_text());assert source['success']
 roots={}
 for region,rows in source['regions'].items():
  for row in rows:
   assert 'Spruce' in row['mesh'] and any('/'+n+'.' in row['actor'] for n in NAMES),row
   roots[tuple(round(v,2) for v in row['root'])]=row['root']
 assert 4<=len(roots)<=10,len(roots);R['roots']=list(roots.values())
 R['main_before']=sha(MAIN);R['connectors_before']=sha(CONNECT)
 ea=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 for name in NAMES:
  package='/Game/Creepwood_Carnival_Meshingun/Environment/Map/'+name
  file=ROOT/('Content'+package[len('/Game'):]+'.umap')
  rec={'before':sha(file),'roots':[]};R['levels'][name]=rec
  for target in (OUT/(name+'.before.umap'),BACKUP/(name+'.before.umap')):
   shutil.copy2(file,target);assert sha(target)==rec['before']
  world=unreal.EditorLoadingAndSavingUtils.load_map(package);assert world
  total=0
  for root in roots.values():
   lo=unreal.Vector(root[0]-25,root[1]-25,root[2]-250);hi=unreal.Vector(root[0]+25,root[1]+25,root[2]+250)
   actors=ea.get_all_level_actors();before=left(actors,lo,hi)
   if not before:rec['roots'].append({'root':root,'already_absent':True});continue
   removed=0
   for actor in components(actors):
    n=unreal.CarnivalRouteEditorLibrary.remove_foliage_in_box(actor,lo,hi,'Spruce');assert n>=0;removed+=n
   for actor in components(actors):
    orphan_names={s.split()[1] for a,s in descriptions([actor],lo,hi) if s.startswith('component') and 'owned_by_record=NO' in s}
    for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
     if comp.get_name() not in orphan_names or not comp.static_mesh or 'Spruce' not in comp.static_mesh.get_name():continue
     ids=comp.get_instances_overlapping_box(unreal.Box(min=lo,max=hi),True)
     inside=[i for i in ids if all(a<=v<=b for a,v,b in zip(lo.to_tuple(),comp.get_instance_transform(i,True).translation.to_tuple(),hi.to_tuple()))]
     for i in sorted(inside,reverse=True):assert comp.remove_instance(i);removed+=1
     actor.modify()
   assert left(ea.get_all_level_actors(),lo,hi)==0,(name,root)
   rec['roots'].append({'root':root,'before_components':before,'removed':removed});total+=removed
  if total:assert unreal.EditorLoadingAndSavingUtils.save_map(world,package)
  world=unreal.EditorLoadingAndSavingUtils.load_map(package);assert world
  for root in roots.values():
   lo=unreal.Vector(root[0]-25,root[1]-25,root[2]-250);hi=unreal.Vector(root[0]+25,root[1]+25,root[2]+250)
   assert left(ea.get_all_level_actors(),lo,hi)==0,(name,'root returned after reload',root)
  rec.update(removed=total,after=sha(file),reload_clean=True)
  shutil.copy2(file,BACKUP/file.name);assert sha(BACKUP/file.name)==rec['after']
 R['main_after']=sha(MAIN);R['connectors_after']=sha(CONNECT)
 assert R['main_after']==R['main_before'] and R['connectors_after']==R['connectors_before']
 R.update(external_backup=str(BACKUP),success=True)
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=2))
