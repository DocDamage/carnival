"""Hole guards: block every channel except Camera (InvisibleWall ignored Visibility, so traces - including the
reachability audit - passed through). Saves only the hospital set-dress level (backed up)."""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_IndustrialHospitalSetDress';LEVEL_FILE=ROOT/('Content/Carnival/World/Levels/'+LEVEL+'.umap')
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/HospitalHoleGuardsRetune_20261001';OUT.mkdir(parents=True,exist_ok=False)
R={'success':False,'errors':[],'guards':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_retune.umap'));R['map_sha256_before']=sha(MAPFILE)
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 gs=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label().startswith('Hospital_HoleGuard')]
 assert gs
 for g in gs:
  c=g.static_mesh_component;g.modify();c.set_collision_profile_name('BlockAll')
  c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA,unreal.CollisionResponseType.ECR_IGNORE)
  R['guards'].append(g.get_actor_label())
 assert unreal.EditorLoadingAndSavingUtils.save_packages([gs[0].get_outermost()],False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before'];R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
