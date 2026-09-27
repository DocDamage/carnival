"""Read-only clearance and continuity audit of the saved connected Carnival world."""
import sys,json,math
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import *
world=unreal.EditorLoadingAndSavingUtils.load_map(CARNIVAL)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors=list(eas.get_all_level_actors())
report={'map':world.get_path_name(),'levels':[x.get_path_name() for x in unreal.EditorLevelUtils.get_levels(world)],
        'actor_count':len(actors),'samples':[],'missing_floor':[],'height_mismatches':[],'obstructions':[],'walkable_floor_contacts':[],
        'dolls':[a.get_actor_label() for a in actors if isinstance(a,unreal.CarnivalHauntedDoll)]}
route=route_manifest()['route_world']
def trace(p):
    hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(p[0],p[1],p[2]+650),unreal.Vector(p[0],p[1],p[2]-1400),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
    return hit.to_tuple() if hit and hit.to_tuple()[0] else None
centers=[]
for i,p in enumerate(route):
    hit=trace(p)
    sample={'i':i,'expected':p}
    if hit:
        sample.update(point=list(hit[5].to_tuple()),actor=hit[9].get_actor_label() if hit[9] else None)
        sample['dz']=hit[5].z-p[2]
        if abs(sample['dz'])>48:report['height_mismatches'].append(sample)
        centers.append(unreal.Vector(p[0],p[1],hit[5].z+99))
    else:
        report['missing_floor'].append(sample);centers.append(None)
    report['samples'].append(sample)
for i in range(len(centers)-1):
    p,q=centers[i],centers[i+1]
    if p is None or q is None:continue
    # A standing character capsule also catches demo walls and low bridge beams.
    hit=unreal.SystemLibrary.capsule_trace_single(world,p,q,43,96,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
    if hit and hit.to_tuple()[0]:
        h=hit.to_tuple()
        contact={'i':i,'actor':h[9].get_actor_label() if h[9] else None,'point':list(h[5].to_tuple()),'normal':list(h[7].to_tuple())}
        # The character's movement component follows walkable ground instead of
        # following a perfectly straight capsule sweep through a convex slope.
        is_floor=h[7].z>math.cos(math.radians(45)) and h[5].z<max(p.z,q.z)-60
        report['walkable_floor_contacts' if is_floor else 'obstructions'].append(contact)
for a in actors:
    if isinstance(a,unreal.CarnivalMotorcycle):
        mesh=a.get_editor_property('bike_mesh')
        report['motorcycle']={'label':a.get_actor_label(),'mesh':str(mesh.get_editor_property('skeletal_mesh_asset')),'rotation':str(a.get_actor_rotation()),'bounds':str(a.get_actor_bounds(False))}
report['success']=not report['missing_floor'] and not report['height_mismatches'] and not report['obstructions']
report['length_m']=route_manifest()['length_m'];report['normal_seconds']=route_manifest()['normal_travel_seconds']
(OUT/'Route_Validation.json').write_text(json.dumps(report,indent=2))
unreal.log('ROUTE_VALIDATION '+json.dumps({k:len(report[k]) for k in ['missing_floor','height_mismatches','obstructions']}))
