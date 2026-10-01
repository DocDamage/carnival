"""Motorcycle (and walk) along the R03-R06 outer spine using the hospital-route runner."""
import json,math,runpy
from pathlib import Path
ROOT=Path(r'F:\Carnival')
src=(ROOT/'Scripts/playtest_world_expansion_walk_routes.py').read_text()
ns={}
# Reuse the walk runner's exact spine geometry (catmull + resample + verified gate-gap override).
exec(compile(src[:src.index('lab=resample(')],'spine_geometry','exec'),ns)
points=[list(p) for p in ns['outer']]
import os
# Optional: drop the Catmull overshoot lobe between authored controls 4-6 (waypoints 36-39)
# to test whether vehicles can take the chord across the corner.
# The walk runner's geometry now drops the overshoot lobe itself (drop_overshoot_lobes).
runpy.run_path(str(ROOT/'Scripts/playtest_industrial_hospital_route.py'),init_globals={
 'WORLD_ROUTE_POINTS':points,'REPORT_PREFIX':os.environ.get('CARNIVAL_SPINE_MOTO_REPORT','OuterSpine_Motorcycle_20261001')},run_name='__main__')
