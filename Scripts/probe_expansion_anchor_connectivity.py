"""Read-only: which expansion anchors/targets a step-aware flood from each start reaches."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
src=(ROOT/'Scripts/find_campaign_station_sites.py').read_text()
src=src[:src.index('\ntry:\n before=')].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(src,'finder_defs','exec'),g)
OUT=ROOT/'Saved/CampaignAcceptance/LabConnectivityAfterRotationFix_20260930';OUT.mkdir(parents=True,exist_ok=False)
TARGETS={'prison_junction':(-30000,-25000),'prison_tower_paintings':(-25900,-34360),'prison_tower_D':(-24120,-35490),'prison_sewer_service':(-27000,-19000),
 'lab_a_anchor':(-41000,-8000),'lab_a_interior':(-42100,-6300),'lab_b_gallery':(-43300,-5000),'lab_b_switchboard':(-42008,-5316),'sewer_entry':(-27000,-12500),'sewer_r11':(-27100,-9654),
 'atlantis_r11':(-19000,-11000),'atlantis_r12':(-7000,-11000),'shipwreck':(-6000,-10000),'docks_north':(-55000,-55000)}
R={'success':False,'errors':[],'assets_saved':False,'starts':[],'limits':'Collision probe at 1 m spacing; not player traversal.'}
try:
 g['world']=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 for label,seed,box in [('lab_a_anchor',(-41000,-8000,600),4000)]:
  g['FRONTIER'].clear();nodes,start=g['flood'](seed,box)
  reached={k:min((math.dist(n,v) for n in nodes),default=None) for k,v in TARGETS.items()}
  R['starts'].append({'start':label,'nodes':len(nodes),'seed_floor_z':nodes[start].z-98 if start else None,
   'nearest_node_to_target_cm':reached,'frontier':g['FRONTIER'].most_common(10)})
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
