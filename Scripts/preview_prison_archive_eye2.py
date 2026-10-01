"""Render prison painting C from the station stand at eye height and from its open front; no saves."""
import runpy,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
art=(-25885,-34358,750);stand=(-25800,-34500,678)
fx,fy=-0.71,-0.71;rx,ry=-fy,fx
cases=[('Stand_Eye',(stand[0],stand[1],stand[2]+70),art),
 ('Front_Open',(art[0]-rx*350,art[1]-ry*350,760),art),
 ('Wide_Behind',(stand[0]+rx*250,stand[1]+ry*250,800),art)]
out='Saved/CampaignAcceptance/PrisonArchiveEyeAfterFlip_20260930'
assert not (ROOT/out).exists()
try:runpy.run_path(str(ROOT/'Scripts/capture_industrial_hospital_connected.py'),init_globals={'CAPTURE_OUTPUT':out,'CAPTURE_OVERRIDE_CASES':cases})
except Exception:traceback.print_exc();unreal.SystemLibrary.quit_editor()
