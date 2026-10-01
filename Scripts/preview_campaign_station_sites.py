"""Render each placed campaign station from behind its stand node; no saves."""
import json,math,runpy,sys
from pathlib import Path
ROOT=Path(r'F:\Carnival');sys.path.insert(0,str(ROOT/'Scripts'))
d=json.loads((ROOT/'Saved/CampaignAcceptance/CampaignStationsAuthored2_20260930/index.json').read_text())
sites={r['station']:r for r in json.loads((ROOT/'Saved/CampaignAcceptance/StationSites8_20260930/index.json').read_text())['stations']}
cases=[]
for p in d['placed']:
 row=sites[p['station']]
 c=row['controls'][0];s=c['stand'];t=c['station']
 dx,dy=s[0]-t[0],s[1]-t[1];l=max(math.hypot(dx,dy),1)
 cam=(s[0]+dx/l*260,s[1]+dy/l*260,s[2]+90)
 cases.append((p['station'],cam,tuple(t)))
out='Saved/CampaignAcceptance/CampaignStationsRendered2_20260930'
assert not (ROOT/out).exists(),'Preserve earlier captures'
runpy.run_path(str(ROOT/'Scripts/capture_industrial_hospital_connected.py'),init_globals={'CAPTURE_OUTPUT':out,'CAPTURE_OVERRIDE_CASES':cases})
