"""Move the confirmed motorcycle blocker off the spine; save only our mansion copy."""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');NAME='L_HauntedMansionConnected'
LEVEL=ROOT/('Content/Carnival/World/Levels/'+NAME+'.umap')
MAIN=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
CONNECT=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
OUT=ROOT/'Saved/WorldExpansion/MansionSpineCardBox_20261029';OUT.mkdir(parents=True,exist_ok=False)
BACKUP=Path(r'D:\CarnivalBackups\20261029_mansion_spine');BACKUP.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;R={'success':False,'errors':[],'candidates':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hit(h):
 d=h.to_tuple() if h else None
 return d if d and d[0] else None
try:
 R['before']={p.name:sha(p) for p in (LEVEL,MAIN,CONNECT)}
 shutil.copy2(LEVEL,OUT/(NAME+'.before.umap'))
 shutil.copy2(LEVEL,BACKUP/(NAME+'.before.umap'))
 assert sha(OUT/(NAME+'.before.umap'))==sha(BACKUP/(NAME+'.before.umap'))==R['before'][LEVEL.name]
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 ea=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors=ea.get_all_level_actors()
 box=next(a for a in actors if a.get_actor_label()=='SM_CardBox10' and '/'+NAME+'.' in a.get_path_name())
 old=box.get_actor_location();assert math.dist(old.to_tuple(),(-68820.748,-83467.999,629.326))<2
 R.update(actor=box.get_path_name(),old=old.to_tuple())
 center,extent=box.get_actor_bounds(False);bottom_offset=center.z-extent.z-old.z
 roads=[a for a in actors if a.get_actor_label().startswith('OuterRoute_Segment')]
 ignore=[box]+[a for a in actors if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 anchors=[a.get_actor_location() for a in actors if 'CarnivalRouteAnchor' in [str(t) for t in a.tags]]
 chosen=None
 for x,y in ((-68500,-82700),(-68200,-82600),(-68800,-82500),(-68100,-82400)):
  # Keep the prop outside the physical slab, with 1.5 m extra clearance.
  near=False
  for road in roads:
   component=road.get_component_by_class(unreal.StaticMeshComponent)
   bounds=component.static_mesh.get_bounding_box();tf=component.get_world_transform()
   q=tf.inverse_transform_location(V(x,y,road.get_actor_location().z));scale=road.get_actor_scale3d()
   if bounds.min.x-150/max(abs(scale.x),.001)<=q.x<=bounds.max.x+150/max(abs(scale.x),.001) and bounds.min.y-150/max(abs(scale.y),.001)<=q.y<=bounds.max.y+150/max(abs(scale.y),.001):
    near=True;break
  if near or min(math.hypot(x-a.x,y-a.y) for a in anchors)<300:
   R['candidates'].append({'xy':[x,y],'rejected':'road or route anchor'});continue
  floor=hit(unreal.SystemLibrary.line_trace_single(world,V(x,y,1200),V(x,y,-200),unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignore,unreal.DrawDebugTrace.NONE,True))
  if not floor or floor[7].z<.7:
   R['candidates'].append({'xy':[x,y],'rejected':'no walkable support'});continue
  stand=floor[5]+V(0,0,100)
  occupied=hit(unreal.SystemLibrary.capsule_trace_single(world,stand,stand+V(0,0,1),55,90,unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignore,unreal.DrawDebugTrace.NONE,True))
  if occupied:
   R['candidates'].append({'xy':[x,y],'rejected':'occupied'});continue
  chosen=V(x,y,floor[5].z-bottom_offset+1)
  R['support']={'actor':floor[9].get_path_name(),'point':floor[5].to_tuple()};break
 assert chosen,'No supported off-road placement found'
 box.modify();box.set_actor_location(chosen,False,True);R['new']=box.get_actor_location().to_tuple()
 assert unreal.EditorLoadingAndSavingUtils.save_packages([box.get_outermost()],False)
 R['after']={p.name:sha(p) for p in (LEVEL,MAIN,CONNECT)}
 assert R['before'][MAIN.name]==R['after'][MAIN.name]
 assert R['before'][CONNECT.name]==R['after'][CONNECT.name]
 shutil.copy2(LEVEL,BACKUP/LEVEL.name);assert sha(BACKUP/LEVEL.name)==sha(LEVEL)
 R['external_backup']=str(BACKUP);R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=2))
