"""Inspect actual proposed reception, ward and records furnishings; no saves."""
import runpy,sys
from pathlib import Path
ROOT=Path(r'F:\Carnival');sys.path.insert(0,str(ROOT/'Scripts'))
from industrial_hospital_route_config import HOSPITAL_YAW,hospital_level_transform,rotate_xy
def wp(p):
 o=hospital_level_transform();x,y=rotate_xy(p,HOSPITAL_YAW)
 return o[0]+x,o[1]+y,o[2]+p[2]
cases=[('ReceptionDesk',wp((5500,700,245)),wp((5708,874,150))),
 ('ReceptionApproach',wp((5200,-200,245)),wp((5708,874,150))),
 ('WardBed',wp((9400,-3500,245)),wp((9617,-3478,145))),
 ('WardApproach',wp((9300,-3100,245)),wp((9617,-3478,145))),
 ('RecordsDesk',wp((1900,1300,245)),wp((1755,1140,150))),
 ('RecordsApproach',wp((2200,500,245)),wp((1755,1140,150)))]
out='Saved/CampaignAcceptance/HospitalSitesRendered_20260930'
assert not (ROOT/out).exists(),'Preserve earlier captures'
runpy.run_path(str(ROOT/'Scripts/capture_industrial_hospital_connected.py'),init_globals={
 'CAPTURE_OUTPUT':out,'CAPTURE_OVERRIDE_CASES':cases})
