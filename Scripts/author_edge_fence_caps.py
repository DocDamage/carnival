"""Cap every edge fence with an invisible 3 m wall.

`playtest_edge_fences.py` showed the 1.14 m railings stop a walking or running player, but a running jump (with the
vault/mantle move) carries the character over them into empty space (the fall net then brings it back). Each
`CarnivalEdgeFence` railing gets a hidden box in its own footprint, 20 cm thick and 3 m tall, with the engine's
`InvisibleWall` profile: it blocks pawns and vehicles but not the camera or Visibility traces (so reachability audits
do not see it). Caps go in the railing's level; both levels are backed up; the persistent map must not change.
"""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
LEVELS={'L_CarnivalWorldExpansion_Connections_Layout':ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap',
        'L_CarnivalWorldExpansion_DocksEast':ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksEast.umap'}
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/EdgeFenceCaps_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TAG='CarnivalEdgeFence';CAP_TAG='CarnivalEdgeFenceCap';HEIGHT=300.0;THICK=20.0;RAIL_LEN=459.0
R={'success':False,'errors':[],'per_level':{}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 R['map_sha256_before']=sha(MAPFILE)
 for lv,f in LEVELS.items():R['per_level'][lv]={'sha256_before':sha(f),'caps':0};shutil.copy2(f,OUT/(lv+'.before_fence_caps.umap'))
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 acts=EA.get_all_level_actors()
 assert not any(CAP_TAG in [str(x) for x in a.tags] for a in acts),'Caps already authored'
 fences=[a for a in acts if TAG in [str(x) for x in a.tags]];assert len(fences)==677,len(fences)
 cube=unreal.load_asset('/Engine/BasicShapes/Cube');assert cube
 for lv in LEVELS:
  mine=[f for f in fences if '/'+lv+'.' in f.get_path_name()]
  if not mine:continue
  assert LE.set_current_level_by_name(lv)
  for f in mine:
   up=f.get_actor_up_vector();loc=f.get_actor_location()+up*(HEIGHT/2)
   c=EA.spawn_actor_from_class(unreal.StaticMeshActor,loc,f.get_actor_rotation());assert c and '/'+lv+'.' in c.get_path_name()
   sm=c.static_mesh_component;sm.set_static_mesh(cube);sm.set_collision_profile_name('InvisibleWall')
   assert str(sm.get_collision_profile_name())=='InvisibleWall'
   c.set_actor_scale3d(V(THICK/100,f.get_actor_scale3d().y*RAIL_LEN/100,HEIGHT/100));c.set_actor_hidden_in_game(True)
   sm.set_editor_property('cast_shadow',False)
   c.set_actor_label('EdgeFenceCap');c.set_folder_path('EdgeFences');c.tags=[unreal.Name(CAP_TAG)]
   R['per_level'][lv]['caps']+=1
 pk=[next(a for a in EA.get_all_level_actors() if CAP_TAG in [str(x) for x in a.tags] and '/'+lv+'.' in a.get_path_name()).get_outermost()
     for lv in LEVELS if R['per_level'][lv]['caps']]
 assert unreal.EditorLoadingAndSavingUtils.save_packages(pk,False)
 for lv,f in LEVELS.items():R['per_level'][lv]['sha256_after']=sha(f)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
