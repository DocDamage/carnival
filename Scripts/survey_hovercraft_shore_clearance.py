"""Read-only full-hull collision survey around the stalled side-pier approach."""
import json
import traceback
from pathlib import Path

import unreal

OUT = Path(r'F:\Carnival\Saved\WorldExpansion\WaterVehicleAcceptance\HovercraftShoreClearance_20261029.json')
V = unreal.Vector
R = {'success': False, 'errors': [], 'sweeps': [], 'nearby_actors': []}
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    assert world
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    ignore = [a for a in actors if a.get_actor_label().startswith('SM_Landscape_Far_01a')
              or isinstance(a, (unreal.CarnivalBoat, unreal.CarnivalHovercraft, unreal.PhysicsVolume))]
    for x in (-50700, -50500, -50315, -50300, -50100, -49900):
        for y in (-48500, -48615, -48700, -48900, -49100, -49500, -50000):
            p = V(x, y, 735)
            raw = unreal.SystemLibrary.box_trace_single_by_profile(world, p, p + V(0, -150, 0),
                V(280, 205, 80), unreal.Rotator(pitch=-2.25, yaw=-90), 'Vehicle', False, ignore,
                unreal.DrawDebugTrace.NONE, True)
            h = raw.to_tuple() if raw else None
            R['sweeps'].append({'start_cm': p.to_tuple(), 'blocked': bool(h and h[0]),
                'blocker': h[9].get_actor_label() if h and h[0] and h[9] else None,
                'actor_path': h[9].get_path_name() if h and h[0] and h[9] else None,
                'component': h[10].get_path_name() if h and h[0] and h[10] else None,
                'impact_cm': h[5].to_tuple() if h and h[0] else None,
                'normal': h[7].to_tuple() if h and h[0] else None,
                'initial_overlap': bool(h[1]) if h and h[0] else False})
    for actor in actors:
        center, extent = actor.get_actor_bounds(False)
        if extent.x > 20000 or extent.y > 20000:
            continue
        if abs(center.x + 50300) <= extent.x + 600 and abs(center.y + 48850) <= extent.y + 600:
            R['nearby_actors'].append({'label': actor.get_actor_label(), 'path': actor.get_path_name(),
                'center_cm': center.to_tuple(), 'extent_cm': extent.to_tuple()})
    R['success'] = True
except Exception:
    R['errors'].append(traceback.format_exc())
    raise
finally:
    OUT.write_text(json.dumps(R, indent=2))
