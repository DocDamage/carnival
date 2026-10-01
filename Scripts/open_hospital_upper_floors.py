"""Open the hospital's upper floors (user decision 2026-10-01).

The source scene sealed both stairwells with InvisibleWall BlockingVolumes (LV_Hospital_Volume) and
debris on the flights/landings. This removes the two volumes and the debris props that obstruct a
standing player on the stairs (StairwellObstructions.json); wall boards, radiators and blinds stay.
Saves LV_Hospital_Volume and L_IndustrialHospitalSetDress only (both backed up).
"""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
FILES={'LV_Hospital_Volume':ROOT/'Content/Hospital_Meshingun/Environment/Map/LV_Hospital_Volume.umap',
 'L_IndustrialHospitalSetDress':ROOT/'Content/Carnival/World/Levels/L_IndustrialHospitalSetDress.umap'}
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/HospitalUpperFloorsOpened_20261001';OUT.mkdir(parents=True,exist_ok=False)
DEBRIS=['SM_Corpse_01d2','SM_BedsideTable_01b7','SM_MedicalBarrier_01c4','SM_MedicalBarrier_01c5','SM_WheelChair_01a13','SM_Rack_01b','BP_Rack_04b2','SM_TrashBasket_01b18',
 'SM_AnMachine_01a3','SM_MedicalBarrier_01d5','BP_TreatmentTable_02d13','SM_Rack_04b','SM_Rack_Drawer_05a','SM_IVStand_01a9','SM_TreatmentTable_02a']
VOLUMES=['BlockingVolume','BlockingVolume2']
R={'success':False,'errors':[],'removed':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 R['map_sha256_before']=sha(MAPFILE)
 for n,f in FILES.items():R[n+'_before']=sha(f);shutil.copy2(f,OUT/(n+'.before_open.umap'))
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 acts=[a for a in EA.get_all_level_actors() if 'Hospital' in a.get_level().get_outermost().get_name()]
 pk={}
 for lab in VOLUMES+DEBRIS:
  hits=[a for a in acts if a.get_actor_label()==lab and (lab not in VOLUMES or isinstance(a,unreal.BlockingVolume))]
  assert len(hits)==1,(lab,len(hits))
  a=hits[0];o,e=a.get_actor_bounds(False);lv=a.get_level().get_outermost()
  R['removed'].append({'label':lab,'class':a.get_class().get_name(),'level':lv.get_name(),'origin':list(o.to_tuple()),'extent':list(e.to_tuple())})
  pk[lv.get_name()]=lv;EA.destroy_actor(a)
 assert unreal.EditorLoadingAndSavingUtils.save_packages(list(pk.values()),False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 for n,f in FILES.items():R[n+'_after']=sha(f)
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
