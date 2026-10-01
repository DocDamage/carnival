"""Clear furniture out of the hospital doorways that left three ground-floor rooms with no way out (they could
only be entered by falling through upper-floor holes). Each blocker is slid sideways along the doorway's wall
(perpendicular to the passage) by the smallest offset that leaves a standing capsule free to pass 2.5 m either
side of the frame, without the prop overlapping walls or other furniture. Saves only the changed hospital
levels (backed up); the persistent map hash is checked unchanged."""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/HospitalDoorwayBlockers_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
PAIRS=[('BP_Door_01a24','SM_Corpse_01b'),('BP_Door_01a23','bench47'),('BP_Door_01a37','BP_BookShelf_03a2'),
 ('BP_Door_02a6','SM_MedicalBarrier_01a17'),('BP_Door_01a29','BP_TreatmentTable_02d7')]
FLOOR=643.0
R={'success':False,'errors':[],'moves':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 R['map_sha256_before']=sha(MAPFILE)
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);acts=EA.get_all_level_actors()
 by={a.get_actor_label():a for a in acts}
 pk={};backed=set()
 def doorway(d):
  fr=[k for k in d.get_components_by_class(unreal.StaticMeshComponent) if k.static_mesh and 'Frame' in k.static_mesh.get_name()]
  fo=unreal.SystemLibrary.get_component_bounds(fr[0])[0] if fr else d.get_actor_location()
  f=d.get_actor_forward_vector();f.z=0;return V(fo.x,fo.y,FLOOR+110),f.normal()
 def clear(c,f,ign):
  return not unreal.SystemLibrary.capsule_trace_single(w,c-f*250,c+f*250,40,85,TQ,False,ign,N,True).to_tuple()[0] if unreal.SystemLibrary.capsule_trace_single(w,c-f*250,c+f*250,40,85,TQ,False,ign,N,True) else True
 for dl,bl in PAIRS:
  d=by[dl];b=by[bl];c,f=doorway(d);side=V(-f.y,f.x,0)
  lvl=b.get_level().get_outermost();name=lvl.get_name().split('/')[-1]
  if name not in backed:
   src=ROOT/('Content'+lvl.get_name()[len('/Game'):]+'.umap');shutil.copy2(src,OUT/(name+'.before_doorways.umap'));backed.add(name);R[name+'_sha_before']=sha(src)
  start=b.get_actor_location();bo,be=b.get_actor_bounds(False)
  rec={'door':dl,'blocker':bl,'level':name,'from':[round(v) for v in start.to_tuple()],'clear_before':clear(c,f,[d])}
  done=False
  # Which side of the doorway centre line the prop already leans to; try that side first.
  pref=1 if (bo-c).dot(side)>=0 else -1
  for dist in range(50,451,25):
   for sg in (pref,-pref):
    off=side*(sg*dist);b.set_actor_location(start+off,False,True)
    if not clear(c,f,[d]):continue
    no,ne=b.get_actor_bounds(False)
    # Prop must not overlap anything except the floor (box raised 6 cm, shrunk 4 cm).
    ov=unreal.SystemLibrary.box_overlap_actors(w,V(no.x,no.y,no.z+6),V(max(1,ne.x-4),max(1,ne.y-4),max(1,ne.z-4)),[unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1,unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2],None,[b,d])
    ov=[a.get_actor_label() for a in ov or [] if not a.get_actor_label().startswith(('Water_','PostProcess','Light','BO_floor','SM_Floor','floor'))]
    if ov:continue
    rec.update(to=[round(v) for v in b.get_actor_location().to_tuple()],offset_cm=sg*dist);done=True;break
   if done:break
  if not done:
   b.set_actor_location(start,False,True);rec['result']='no clear placement; left in place'
  else:
   b.modify();rec['result']='moved';pk[name]=lvl
  rec['clear_after']=clear(c,f,[d]);R['moves'].append(rec)
 if pk:assert unreal.EditorLoadingAndSavingUtils.save_packages(list(pk.values()),False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 R['saved']=list(pk);R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
