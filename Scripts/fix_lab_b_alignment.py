"""Place Lab B so its open front (removed gate, local (1425,400)) meets Lab A's west opening
(removed SM_MWall03-700x350-8, Lab A local (-1423,400)). Both rooms share one layout, so Lab B
keeps Lab A's yaw (-57) at Lab A-local (-2848, 0). The previous 123-degree placement folded
Lab B back over Lab A. Saves only the root map (backed up); sublevel packages stay unchanged."""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
LAB_A=(-42097.962876199206,-7043.716818882417,600.0);YAW=-57.0
OUT=ROOT/'Saved/WorldExpansion/LabBAlignmentFix_20260930';OUT.mkdir(parents=True,exist_ok=False)
R={'success':False,'errors':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 c,s=math.cos(math.radians(YAW)),math.sin(math.radians(YAW));lx,ly=-2848.0,0.0
 target=(LAB_A[0]+c*lx-s*ly,LAB_A[1]+s*lx+c*ly,LAB_A[2])
 lab_b_file=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB.umap'
 R.update(map_sha256_before=sha(MAPFILE),lab_b_sha256_before=sha(lab_b_file),new_translation=target,new_yaw=YAW)
 shutil.copy2(MAPFILE,OUT/'LV_Carnival.before_lab_b_alignment.umap')
 world=unreal.EditorLoadingAndSavingUtils.load_map(MAP);assert world
 st=unreal.GameplayStatics.get_streaming_level(world,'/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB');assert st
 old=st.get_editor_property('level_transform');r=old.rotation.rotator()
 R['old']={'translation':list(old.translation.to_tuple()),'rotation':[r.roll,r.pitch,r.yaw]}
 t=unreal.Transform();t.set_editor_property('translation',unreal.Vector(*target))
 t.set_editor_property('rotation',unreal.Rotator(roll=0.0,pitch=0.0,yaw=YAW).quaternion());t.set_editor_property('scale3d',old.scale3d)
 st.modify();st.set_editor_property('level_transform',t)
 assert unreal.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
 R.update(map_sha256_after=sha(MAPFILE),lab_b_sha256_after=sha(lab_b_file))
 assert R['lab_b_sha256_after']==R['lab_b_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
