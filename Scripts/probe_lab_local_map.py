"""Read-only: Lab A local-frame map (50 cm) of flood reach vs standing-clear floor, across the west opening into Lab B."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
src=(ROOT/'Scripts/find_campaign_station_sites.py').read_text()
src=src[:src.index('\ntry:\n before=')].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(src,'finder_defs','exec'),g)
V=unreal.Vector;A=(-42097.962876199206,-7043.716818882417);YAW=math.radians(-57)
def world(lx,ly):return (A[0]+math.cos(YAW)*lx-math.sin(YAW)*ly,A[1]+math.sin(YAW)*lx+math.cos(YAW)*ly)
R={'success':False,'errors':[]}
try:
 g['world']=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 g['WALK_IGNORE'].extend(a for a in acts if a.get_actor_label().startswith('BP_MGate01'))
 nodes,start=g['flood']((-41000,-8000,600),6500,50)
 rows=[]
 for ly in range(1500,-801,-50):
  row=''
  for lx in range(-4300,1551,50):
   wx,wy=world(lx,ly)
   near=min((abs(k[0]-wx)+abs(k[1]-wy) for k in ((round(wx/50)*50+dx,round(wy/50)*50+dy) for dx in (-50,0,50) for dy in (-50,0,50)) if k in nodes),default=None)
   if near is not None and near<=60:row+='R';continue
   f=g['floor_at'](wx,wy,900,450)
   if not f:row+=' ';continue
   c=f+V(0,0,98);row+=('o' if not g['capsule_hit'](c,c+V(1,0,0)) else '#')
  rows.append(f'{ly:5d} '+row)
 R.update(rows=rows,success=True)
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(ROOT/'Saved/CampaignAcceptance/LabLocalMap_20260930.json').write_text(json.dumps(R,indent=1))
