"""Fence every walkable edge that drops into empty space (user decision 2026-10-01: fall net + edge fences).

About 1.1 km of the OuterRoute spine and the East Dock stand over nothing (`probe_spine_ground.py`). For each top
edge of the spine segments and of the East Dock surfaces (including the new boatyard basin and slipways), samples
1 m beyond the edge every railing length: when nothing lies within 60 m below (at two of three points per piece), a
Docks-pack pier railing (`SM_Pier_Railing_F`, 1.14 m, convex collision) is placed 20 cm inside the edge, following
the edge's slope. Edges beside another surface (a junction, the next segment, a deck) or above real ground stay open.
Fences go into the level of the surface they guard; both levels are backed up and the persistent map must not change.
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
LEVELS={'L_CarnivalWorldExpansion_Connections_Layout':ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap',
        'L_CarnivalWorldExpansion_DocksEast':ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksEast.umap'}
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/WalkableEdgeFences_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
RAIL='/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_F';RAIL_LEN=459.0;TAG='CarnivalEdgeFence';DROP=6000.0
TARGET_PREFIX=('OuterRoute_Segment','EastDock_Quay_Approach','EastDock_Main_Quay','EastDock_Through_Walk','EastDock_Loading_Finger',
 'EastDock_Finger_Link_West','EastDock_Finger_Link_Centre','EastDock_Finger_Link_East','EastDock_Boatyard_Basin_Floor','EastDock_Boatyard_Slipway_')
R={'success':False,'errors':[],'targets':0,'edges':0,'pieces':0,'fences':[],'per_level':{}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 R['map_sha256_before']=sha(MAPFILE)
 for lv,f in LEVELS.items():R['per_level'][lv]={'sha256_before':sha(f),'fences':0};shutil.copy2(f,OUT/(lv+'.before_edge_fences.umap'))
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 acts=EA.get_all_level_actors()
 assert not any(TAG in [str(x) for x in a.tags] for a in acts),'Edge fences already authored'
 ign=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 targets=[a for a in acts if a.get_actor_label().startswith(TARGET_PREFIX) and a.get_component_by_class(unreal.StaticMeshComponent)
          and a.get_level().get_outermost().get_name().split('/')[-1] in LEVELS]
 R['targets']=len(targets);rail=unreal.load_asset(RAIL);assert rail
 plan=[]
 for a in targets:
  lv=a.get_level().get_outermost().get_name().split('/')[-1]
  c=a.get_component_by_class(unreal.StaticMeshComponent);b=c.static_mesh.get_bounding_box();tf=a.get_actor_transform()
  top=[tf.transform_location(V(x,y,b.max.z)) for x,y in ((b.min.x,b.min.y),(b.max.x,b.min.y),(b.max.x,b.max.y),(b.min.x,b.max.y))]
  ctr=V(sum(p.x for p in top)/4,sum(p.y for p in top)/4,sum(p.z for p in top)/4)
  up=a.get_actor_up_vector()
  for k in range(4):
   p0,p1=top[k],top[(k+1)%4];e=p1-p0;L=e.length()
   if L<100:continue
   d=e*(1.0/L);mid=(p0+p1)*0.5;o=V(mid.x-ctr.x,mid.y-ctr.y,0);o=o*(1.0/max(o.length(),1e-3))
   R['edges']+=1;n=max(1,math.ceil(L/RAIL_LEN));plen=L/n
   for i in range(n):
    m=p0+d*((i+0.5)*plen);void=0
    for f in (-0.4,0.0,0.4):
     q=m+d*(f*plen)+o*100
     h=t(unreal.SystemLibrary.line_trace_single(w,V(q.x,q.y,q.z+150),V(q.x,q.y,q.z-DROP),TQ,False,ign+[a],N,True))
     if not h:void+=1
    R['pieces']+=1
    if void>=2:plan.append((lv,a.get_actor_label(),m-o*20,d,up,plen))
 for lv in LEVELS:
  mine=[p for p in plan if p[0]==lv]
  if not mine:continue
  assert LE.set_current_level_by_name(lv)
  for _,src,m,d,up,plen in mine:
   rot=unreal.MathLibrary.make_rot_from_yz(d,up)
   f=EA.spawn_actor_from_class(unreal.StaticMeshActor,m,rot);assert f and '/'+lv+'.' in f.get_path_name()
   f.static_mesh_component.set_static_mesh(rail);f.static_mesh_component.set_collision_profile_name('BlockAll')
   f.set_actor_scale3d(V(1,plen/RAIL_LEN,1));f.set_actor_label('EdgeFence_'+src);f.set_folder_path('EdgeFences');f.tags=[unreal.Name(TAG)]
   R['per_level'][lv]['fences']+=1;R['fences'].append({'level':lv,'guards':src,'at':[round(v) for v in m.to_tuple()],'len':round(plen)})
 pk=[]
 for lv in LEVELS:
  if R['per_level'][lv]['fences']:
   x=next(a for a in EA.get_all_level_actors() if TAG in [str(t_) for t_ in a.tags] and '/'+lv+'.' in a.get_path_name());pk.append(x.get_outermost())
 assert unreal.EditorLoadingAndSavingUtils.save_packages(pk,False)
 for lv,f in LEVELS.items():R['per_level'][lv]['sha256_after']=sha(f)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
