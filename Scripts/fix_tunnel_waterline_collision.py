"""SewerToAtlantis_Waterline kept its BlockAll profile on reload (set_collision_enabled is overridden by the
profile), which stopped walkers at the waterline. Set the NoCollision profile. Saves only the connectors level."""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');CONN='L_CarnivalWorldExpansion_Connections_Layout';CONN_FILE=ROOT/('Content/Carnival/World/Levels/'+CONN+'.umap')
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/TunnelWaterlineCollision_20261001';OUT.mkdir(parents=True,exist_ok=False)
R={'success':False,'errors':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 shutil.copy2(CONN_FILE,OUT/(CONN+'.before.umap'));R['map_sha256_before']=sha(MAPFILE)
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 a=next(x for x in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if x.get_actor_label()=='SewerToAtlantis_Waterline')
 c=a.static_mesh_component;R['before']=[str(c.get_collision_profile_name()),str(c.get_collision_enabled())]
 a.modify();c.set_collision_profile_name('NoCollision');R['after']=[str(c.get_collision_profile_name()),str(c.get_collision_enabled())]
 assert unreal.EditorLoadingAndSavingUtils.save_packages([a.get_outermost()],False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before'];R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
