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
start_mode=os.environ.get('CARNIVAL_SPINE_START_MODE','walk')
if start_mode not in ('walk','motorcycle'):raise ValueError('Unknown outer-spine start mode: '+start_mode)
if os.environ.get('CARNIVAL_SPINE_END_INDEX'):
 points=points[:int(os.environ['CARNIVAL_SPINE_END_INDEX'])]
 if len(points)<2:raise ValueError('Outer-spine diagnostic needs at least two points')
# Optional: drop the Catmull overshoot lobe between authored controls 4-6 (waypoints 36-39)
# to test whether vehicles can take the chord across the corner.
# The walk runner's geometry now drops the overshoot lobe itself (drop_overshoot_lobes).
runpy.run_path(str(ROOT/'Scripts/playtest_industrial_hospital_route.py'),init_globals={
 'WORLD_ROUTE_POINTS':points,'START_MODE':start_mode,
 'REPORT_PREFIX':os.environ.get('CARNIVAL_SPINE_MOTO_REPORT','OuterSpine_Motorcycle_20261001')},run_name='__main__')
