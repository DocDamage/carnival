"""Render the prison approach: the spine rock blocker and the showcase planes; no saves."""
import runpy,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
cases=[('Spine_Rock_FromRoad',(-36500,-31700,900),(-34300,-29480,800)),
 ('Prison_Overview_High',(-42000,-42000,9000),(-29000,-29000,600)),
 ('Plane3_FromLabs',(-41000,-8600,900),(-25200,-15400,-500)),
 ('Plane_Strip_FarView',(-60000,-20000,4000),(-37671,-27872,580))]
out='Saved/WorldExpansion/PrisonOverview_20261001'
assert not (ROOT/out).exists()
try:runpy.run_path(str(ROOT/'Scripts/capture_industrial_hospital_connected.py'),init_globals={'CAPTURE_OUTPUT':out,'CAPTURE_OVERRIDE_CASES':cases})
except Exception:traceback.print_exc();unreal.SystemLibrary.quit_editor()
