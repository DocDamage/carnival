"""Render the prison archive from its stand node and the tower interior; no saves."""
import runpy
from pathlib import Path
ROOT=Path(r'F:\Carnival')
stand=(-25800,-34500,678)
cases=[('PrisonArchive_FromStand',(stand[0],stand[1]+60,stand[2]+70),(-25885,-34358,983)),
 ('PrisonArchive_Wide',(-25400,-34000,820),(-25885,-34358,900)),
 ('PrisonTower_Interior',(-26300,-33700,900),(-26500,-34300,700))]
out='Saved/CampaignAcceptance/PrisonArchiveRendered_20260930'
assert not (ROOT/out).exists()
runpy.run_path(str(ROOT/'Scripts/capture_industrial_hospital_connected.py'),init_globals={'CAPTURE_OUTPUT':out,'CAPTURE_OVERRIDE_CASES':cases})
