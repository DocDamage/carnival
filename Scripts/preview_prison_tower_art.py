"""Render the prison main-tower and tower paintings from their open (left) side; no saves."""
import json,runpy,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
art={r['label']:r for r in json.loads((ROOT/'Saved/CampaignAcceptance/PrisonTowerArt_20260930.json').read_text())}
cases=[]
for k in ('WorldExpansion_WallArt_Prison_MainTower_C','WorldExpansion_WallArt_Prison_Tower_D','WorldExpansion_WallArt_Prison_Tower_G'):
 r=art[k];x,y,z=r['loc'][:3];fx,fy=r['forward'][0],r['forward'][1];rx,ry=-fy,fx  # UE right = forward turned +90 yaw
 cases.append((k.split('_')[-2]+'_'+k.split('_')[-1]+'_Front',(x-rx*700,y-ry*700,z),(x,y,z)))
 cases.append((k.split('_')[-2]+'_'+k.split('_')[-1]+'_FromGround',(x-rx*700,y-ry*700,760),(x,y,z)))
out='Saved/CampaignAcceptance/PrisonTowerArtRendered_20260930'
assert not (ROOT/out).exists()
try:
 runpy.run_path(str(ROOT/'Scripts/capture_industrial_hospital_connected.py'),init_globals={'CAPTURE_OUTPUT':out,'CAPTURE_OVERRIDE_CASES':cases})
except Exception:
 traceback.print_exc();unreal.SystemLibrary.quit_editor()
