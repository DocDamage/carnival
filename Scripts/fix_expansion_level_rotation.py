"""Correct three expansion sublevels whose intended yaw was saved as pitch.

connect_world_expansion.py passed yaw positionally to unreal.Rotator(roll, pitch, yaw),
so Prison (-45), Lab A (-57) and Lab B (123) were pitched instead of turned. This sets
each streaming transform to its intended yaw at the same translation and saves only
the root map (backed up). Sublevel packages are not saved and must stay unchanged.
"""
import hashlib,json,shutil,time,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/LevelRotationFix_20260930';OUT.mkdir(parents=True,exist_ok=False)
FIX={'/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison':-45.0,
 '/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabA':-57.0,
 '/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB':123.0}
R={'success':False,'errors':[],'levels':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sub={p:ROOT/('Content'+p[len('/Game'):]+'.umap') for p in FIX}
try:
 R['map_sha256_before']=sha(MAPFILE);R['sublevel_sha256_before']={p:sha(f) for p,f in sub.items()}
 backup=OUT/'LV_Carnival.before_rotation_fix.umap';shutil.copy2(MAPFILE,backup);R['backup']=str(backup)
 world=unreal.EditorLoadingAndSavingUtils.load_map(MAP);assert world
 for pkg,yaw in FIX.items():
  s=unreal.GameplayStatics.get_streaming_level(world,pkg);assert s,pkg
  old=s.get_editor_property('level_transform');r=old.rotation.rotator()
  new=unreal.Transform();new.set_editor_property('translation',old.translation)
  new.set_editor_property('rotation',unreal.Rotator(roll=0.0,pitch=0.0,yaw=yaw).quaternion())
  new.set_editor_property('scale3d',old.scale3d)
  s.modify();s.set_editor_property('level_transform',new)
  R['levels'].append({'package':pkg,'translation':list(old.translation.to_tuple()),'old_rotation':[r.roll,r.pitch,r.yaw],'new_yaw':yaw})
 assert unreal.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False),'Root map save failed'
 R['map_sha256_after']=sha(MAPFILE);R['sublevel_sha256_after']={p:sha(f) for p,f in sub.items()}
 assert R['sublevel_sha256_after']==R['sublevel_sha256_before'],'A sublevel package changed'
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
