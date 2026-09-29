"""Read-only approach-corridor support, camera clearance and wall-art sightline survey."""
import json
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
MAP = '/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB'
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError('Lab B failed to load')
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
report = {'map': MAP, 'nearby_geometry': [], 'samples': [], 'sightlines': []}

def trace(start, end, ignore=None):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(*start), unreal.Vector(*end),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore or [], unreal.DrawDebugTrace.NONE, True)
    row = hit.to_tuple() if hit else None
    return {'hit': bool(row and row[0]), 'point': list(row[4].to_tuple()) if row and row[0] else None,
            'actor': row[9].get_actor_label() if row and row[0] and row[9] else None}

for actor in actors:
    center, extent = actor.get_actor_bounds(False, True)
    if center.x + extent.x > 700 and center.x - extent.x < 1400 and center.y + extent.y > 50 and center.y - extent.y < 750:
        report['nearby_geometry'].append({'label': actor.get_actor_label(), 'class': actor.get_class().get_name(),
            'center': list(center.to_tuple()), 'extent': list(extent.to_tuple())})
for x in (775, 900, 1050, 1200, 1325):
    for y in (250, 400, 550):
        floor = trace((x,y,250), (x,y,-100))
        hit = unreal.SystemLibrary.capsule_trace_single(world, unreal.Vector(x,y,100), unreal.Vector(x,y,101),
            42., 90., unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True)
        row = hit.to_tuple() if hit else None
        report['samples'].append({'position': [x,y,100], 'floor': floor,
            'capsule_blocker': row[9].get_actor_label() if row and row[0] and row[9] else None})
        for wall_y in (56,744):
            report['sightlines'].append({'eye': [x,y,170], 'target': [x,wall_y,200],
                'trace': trace((x,y,170), (x,wall_y,200))})
destination = ROOT/'Saved/WorldExpansion/LabB_Gallery_Survey.json'
destination.write_text(json.dumps(report, indent=2))
print('LAB_B_GALLERY_SURVEY', destination)
unreal.SystemLibrary.quit_editor()
