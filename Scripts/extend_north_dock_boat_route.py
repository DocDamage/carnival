"""Extend the boat activity within freshly surveyed water; save North Dock only.

Solid boarding-deck samples are kept as obstacles, never accepted as deep
water. Native keel checks and hull sweeps still reject these obstructions.
The saved route requires a separate normal-speed lifecycle/boundary playtest.
"""
import copy
import hashlib
import json
import os
import shutil
import traceback
from pathlib import Path

import unreal

ROOT = Path(r'F:\Carnival')
BASE = ROOT / 'Saved/WorldExpansion/WaterVehicleAcceptance'
SURVEY = BASE / os.environ.get('CARNIVAL_BOAT_DEPTH_REPORT', 'NorthDockRouteDepth_20261029_v3.json')
REVISION = os.environ.get('CARNIVAL_BOAT_ROUTE_REVISION', '20261029_v2')
assert REVISION.replace('_', '').isalnum()
OUT = BASE / ('NorthDockBoatRoute_' + REVISION)
BACKUP = Path(r'D:\CarnivalBackups') / ('north_dock_boat_route_' + REVISION)
NAME = 'L_CarnivalWorldExpansion_DocksNorth_Layout'
LEVEL = ROOT / ('Content/Carnival/World/Levels/' + NAME + '.umap')
MAIN = ROOT / 'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
CONNECT = ROOT / 'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
EAST = ROOT / 'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksEast.umap'
OUT.mkdir(parents=True, exist_ok=False)
BACKUP.mkdir(parents=True, exist_ok=False)
R = {'success': False, 'errors': [], 'navigation_samples': 0}
V = unreal.Vector


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


try:
    survey = json.loads(SURVEY.read_text())
    assert survey['success'] and survey['engine_exit_code'] == 0 and not survey['errors']
    assert survey['terrain_trace_ignored_vehicles'], 'Requires terrain survey excluding the saved vehicles'
    rows = {tuple(s['query_xy_cm']): s for s in survey['samples']}
    depths, obstacles = [], []
    # The selected rectangle is inset 1 m from this complete 2 m sample grid.
    for x in range(-49400, -46799, 200):
        for y in range(-59600, -56799, 200):
            row = rows[(x, y)]
            assert row.get('query_succeeded') and row.get('same_body_overlap'), (x, y, 'water membership')
            ground = row['ground']
            assert ground and not ground['initial_overlap']
            assert abs(row['surface_cm'][2] + 240) < .1
            if ground['actor'].startswith('Boat_NorthDock_Inflatable_BoardingDeck_'):
                obstacles.append({'xy_cm': [x, y], 'actor': ground['actor']})
            else:
                assert ground['depth_below_surface_cm'] >= 200, (x, y, ground)
                depths.append(ground['depth_below_surface_cm'])
    R.update(survey_sha256=sha(SURVEY), open_water_samples=len(depths),
             minimum_open_water_depth_cm=min(depths), solid_obstacle_samples=obstacles)
    plan = json.loads((BASE / 'PlacementPlan.json').read_text())
    entry = copy.deepcopy(next(e for e in plan['entries'] if e['kind'] == 'boat'))
    entry.update(navigable_water_min_world_cm=[-49300, -59500],
                 navigable_water_max_world_cm=[-46900, -56900], drive_distance_cm=2000,
                 checkpoints_world_cm=[[-49000, -59200, -240], [-49000, -57200, -240]],
                 drive_lane_survey_evidence={'file': SURVEY.name, 'sample_count': len(depths),
                     'minimum_terrain_depth_cm': min(depths), 'grid_spacing_cm': 200},
                 activity_description='Board the inflatable, follow the channel marker, then reverse to the low berth and unload onto the dock.')
    R['route_entry'] = entry
    R['before'] = {p.name: sha(p) for p in (LEVEL, MAIN, CONNECT, EAST)}
    for target in (OUT / (NAME + '.before.umap'), BACKUP / (NAME + '.before.umap')):
        shutil.copy2(LEVEL, target)
        assert sha(target) == R['before'][LEVEL.name]
    world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    assert world
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    boat = next(a for a in actors if a.get_actor_label() == entry['label'])
    assert '/' + NAME + '.' in boat.get_path_name()
    assert boat.get_editor_property('use_navigable_water_bounds')
    R['old_bounds'] = [boat.get_editor_property('navigable_water_min').to_tuple(),
                       boat.get_editor_property('navigable_water_max').to_tuple()]
    boat.modify()
    boat.set_editor_property('navigable_water_min', unreal.Vector2D(*entry['navigable_water_min_world_cm']))
    boat.set_editor_property('navigable_water_max', unreal.Vector2D(*entry['navigable_water_max_world_cm']))
    # Check the full hull, bank/pitch and wave extremes along the actual lane.
    for y in range(-59200, -57199, 50):
        for z in (-252, -228):
            for pitch in (-2, 8):
                for roll in (-2, 2):
                    assert boat.is_water_transform_navigable(V(-49000, y, z),
                        unreal.Rotator(yaw=-90, pitch=pitch, roll=roll)), (y, z, pitch, roll)
                    R['navigation_samples'] += 1
    # The native guard must still reject the dock and all outer bounds.
    rejected = [(-49400, -58200), (-46800, -58200), (-48100, -59600),
                (-48100, -56800), (-49300, -57200)]
    for x, y in rejected:
        assert not boat.is_water_transform_navigable(V(x, y, -240), unreal.Rotator(yaw=-90)), (x, y)
    R['rejected_obstacle_and_boundary_queries'] = rejected
    author = json.loads((BASE / 'Authoring.json').read_text())
    activity_name = next(v['activity'].split('.')[-1] for v in author['vehicles'] if v['label'] == entry['label'])
    activity = next(a for a in actors if a.get_name() == activity_name and '/' + NAME + '.' in a.get_path_name())
    activity.modify()
    checkpoints = []
    for point, description in zip(entry['checkpoints_world_cm'], ('Reach the channel marker.', 'Reverse to the low berth.')):
        checkpoint = unreal.CarnivalActivityCheckpoint()
        checkpoint.set_editor_property('location', V(*point))
        checkpoint.set_editor_property('radius', float(entry['checkpoint_radius_cm']))
        checkpoint.set_editor_property('description', description)
        checkpoints.append(checkpoint)
    activity.set_editor_property('checkpoints', checkpoints)
    assert unreal.EditorLoadingAndSavingUtils.save_packages([boat.get_outermost()], False)
    R['after'] = {p.name: sha(p) for p in (LEVEL, MAIN, CONNECT, EAST)}
    for p in (MAIN, CONNECT, EAST):
        assert R['after'][p.name] == R['before'][p.name]
    shutil.copy2(LEVEL, BACKUP / LEVEL.name)
    assert sha(BACKUP / LEVEL.name) == R['after'][LEVEL.name]
    R.update(success=True, external_backup=str(BACKUP))
except Exception:
    R['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT / 'index.json').write_text(json.dumps(R, indent=2))
