"""Render Lab A/B interior views after the level-rotation fix; no saves."""
import runpy
from pathlib import Path
ROOT=Path(r'F:\Carnival')
cases=[('LabA_EntryToRoom',(-41300,-7700,820),(-41900,-6700,700)),
 ('LabA_RoomToDisplays',(-41700,-7000,820),(-42100,-6200,750)),
 ('LabA_Overhead',(-41600,-7300,1150),(-41900,-6500,600)),
 ('LabB_FromLabA',(-42300,-6000,820),(-42900,-5300,700)),
 ('LabB_Gallery',(-43000,-5600,820),(-43400,-5000,800)),
 ('Prison_TowerArt',(-25500,-34000,790),(-25850,-34400,700))]
out='Saved/CampaignAcceptance/LabInteriorsAfterRotationFix_20260930'
assert not (ROOT/out).exists()
runpy.run_path(str(ROOT/'Scripts/capture_industrial_hospital_connected.py'),init_globals={'CAPTURE_OUTPUT':out,'CAPTURE_OVERRIDE_CASES':cases})
