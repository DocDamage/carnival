"""Repair the outer spine's two route junctions in the connectors level.

Mansion end: segments 0-3 overlay the last of the R02 trail 44-99 cm above flat ground, blocking it
(PIE stall at (-68627,-82904)). They are laid flat 2 cm above the ground, and segments 4-6 are
re-pitched into a straight ramp to segment 7's near edge; segment 7 onward is unchanged.
Hospital end: 15 spine slabs only duplicate the hospital road 15-25 cm above it, where the
motorcycle wedges (StaticMeshActor_1163). They are removed. Only the connectors level is saved.
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_CarnivalWorldExpansion_Connections_Layout'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/SpineJunctionFix_20261001';OUT.mkdir(parents=True,exist_ok=False)
CLS=json.loads((ROOT/'Saved/WorldExpansion/SpineSegmentClassification_20261001.json').read_text())
HOSPITAL=(95659,128400);HALF_T=22.5
R={'success':False,'errors':[],'reprofiled':[],'removed':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def duplicate(s):
 u=[x for x in s['under'] if x]
 return len(u)==9 and all(x['walk'] for x in u) and all(-5<=s['top']-x['z']<=40 for x in u)
try:
 R.update(level_sha256_before=sha(LEVEL_FILE),map_sha256_before=sha(MAPFILE));shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_junction_fix.umap'))
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 segs={a.get_name():a for a in EA.get_all_level_actors() if a.get_actor_label()=='OuterRoute_Segment' and '/'+LEVEL+'.' in a.get_path_name()}
 S=[segs['StaticMeshActor_%d'%i] for i in range(8)]
 c=[a.get_actor_location() for a in S];L=[a.get_actor_scale3d().x*100 for a in S]
 d=[0.0]
 for i in range(1,8):d.append(d[-1]+math.dist((c[i].x,c[i].y),(c[i-1].x,c[i-1].y)))
 p7=S[7].get_actor_rotation().pitch
 A=(d[3]+L[3]/2,602.0);B=(d[7]-L[7]/2,c[7].z+HALF_T-math.tan(math.radians(p7))*L[7]/2)
 slope=(B[1]-A[1])/(B[0]-A[0])
 for i in range(7):
  a=S[i];r=a.get_actor_rotation();old=(list(c[i].to_tuple()),r.pitch)
  if i<=3:top,pitch=602.0,0.0
  else:top,pitch=A[1]+slope*(d[i]-A[0]),math.degrees(math.atan(slope))
  a.modify();a.set_actor_location(unreal.Vector(c[i].x,c[i].y,top-HALF_T),False,True)
  a.set_actor_rotation(unreal.Rotator(roll=r.roll,pitch=pitch,yaw=r.yaw),True)
  R['reprofiled'].append({'name':a.get_name(),'old_center':old[0],'old_pitch':old[1],'new_top':top,'new_pitch':pitch})
 R['ramp']={'start':A,'end':B,'slope_deg':math.degrees(math.atan(slope))}
 for s in CLS['segments']:
  if duplicate(s) and math.dist(s['origin'][:2],HOSPITAL)<12000:
   a=segs.get(s['name']);assert a,s['name']
   R['removed'].append({'name':s['name'],'origin':s['origin'],'top':s['top'],'under':sorted({x['actor'] for x in s['under'] if x})});EA.destroy_actor(a)
 assert len(R['removed'])==15
 assert unreal.EditorLoadingAndSavingUtils.save_packages([S[0].get_outermost()],False)
 R.update(level_sha256_after=sha(LEVEL_FILE),map_sha256_after=sha(MAPFILE));assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
