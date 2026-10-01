"""Render each placed campaign station from behind its stand node; no saves."""
import json,math,runpy,sys
from pathlib import Path
ROOT=Path(r'F:\Carnival');sys.path.insert(0,str(ROOT/'Scripts'))
d=json.loads((ROOT/'Saved/CampaignAcceptance/CampaignStationsAuthored3_20260930/index.json').read_text())
sites={r['station']:r for r in json.loads((ROOT/'Saved/CampaignAcceptance/StationSites14_20260930/index.json').read_text())['stations']}
cases=[]
for p in d['placed']:
 row=sites[p['station']]
 c=row['controls'][0];s=c['stand'];t=c['station']
 dx,dy=s[0]-t[0],s[1]-t[1];l=max(math.hypot(dx,dy),1)
 cam=(s[0]+dx/l*260,s[1]+dy/l*260,s[2]+90)
 cases.append((p['station'],cam,tuple(t)))
out='Saved/CampaignAcceptance/CampaignStationsRendered3_20260930'
assert not (ROOT/out).exists(),'Preserve earlier captures'
import math as _m
A=(-42097.962876199206,-7043.716818882417);Y=_m.radians(-57)
def W(lx,ly,z):return (A[0]+_m.cos(Y)*lx-_m.sin(Y)*ly,A[1]+_m.sin(Y)*lx+_m.cos(Y)*ly,z)
cases.append(('LabA_WestOpening_FromPlatform',W(-900,400,830),W(-1700,400,640)))
cases.append(('LabA_WestOpening_FromLabB',W(-2100,250,800),W(-1300,450,690)))
cases.append(('LabA_MainRoom_Foliage',W(1000,400,820),W(-600,300,750)))
runpy.run_path(str(ROOT/'Scripts/capture_industrial_hospital_connected.py'),init_globals={'CAPTURE_OUTPUT':out,'CAPTURE_OVERRIDE_CASES':cases})
