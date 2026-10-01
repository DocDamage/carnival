"""Read-only: floor z, standing and edge checks along Lab A local y=200/400/600 from x=-2400 to -900 (50 cm)."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
src=(ROOT/'Scripts/find_campaign_station_sites.py').read_text()
src=src[:src.index('\ntry:\n before=')].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(src,'finder_defs','exec'),g)
V=unreal.Vector;A=(-42097.962876199206,-7043.716818882417);YAW=math.radians(-57)
def world(lx,ly):return (A[0]+math.cos(YAW)*lx-math.sin(YAW)*ly,A[1]+math.sin(YAW)*lx+math.cos(YAW)*ly)
R={'success':False,'errors':[],'lines':{}}
try:
 g['world']=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 for ly in (200,400,600):
  out=[];prev=None
  for lx in range(-900,-2451,-50):
   wx,wy=world(lx,ly);f=g['floor_at'](wx,wy,900,450)
   h=g['t'](unreal.SystemLibrary.line_trace_single(g['world'],V(wx,wy,900),V(wx,wy,450),g['TQ'],False,[],g['NONE'],True))
   e={'lx':lx,'floor':round(f.z,1) if f else None,'top_hit':[round(h[5].z,1),round(h[7].z,2),g['name'](h)] if h else None}
   if f:
    c=f+V(0,0,98);b=g['capsule_hit'](c,c+V(1,0,0));e['standing']=g['name'](b) if b else 'clear'
    if prev:e['edge']=g['edge_ok'](prev,c);e['dz']=round(c.z-prev.z,1)
    prev=c if not b else None
   else:prev=None
   out.append(e)
  R['lines'][ly]=out
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(ROOT/'Saved/CampaignAcceptance/LabJunctionProfile_20260930.json').write_text(json.dumps(R,indent=1))
