"""The foyer clue note was set with positional Rotator(0.0, 14.0, 0.0) (pitch 14); it should lie flat,
turned 14 degrees. Only the persistent map is saved (backed up)."""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/MissionAuthoring/FoyerNoteRotationFix_20261001';OUT.mkdir(parents=True,exist_ok=False)
R={'success':False,'errors':[]}
try:
 shutil.copy2(MAPFILE,OUT/'LV_Carnival.before_note_fix.umap');R['map_sha256_before']=hashlib.sha256(MAPFILE.read_bytes()).hexdigest()
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 note=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='Mission_Foyer_Eli_Physical_Note')
 r=note.get_actor_rotation();R['before']=[r.roll,r.pitch,r.yaw]
 note.modify();note.set_actor_rotation(unreal.Rotator(roll=0.0,pitch=0.0,yaw=14.0),False)
 r=note.get_actor_rotation();R['after']=[r.roll,r.pitch,r.yaw]
 assert unreal.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
 R['map_sha256_after']=hashlib.sha256(MAPFILE.read_bytes()).hexdigest();R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
