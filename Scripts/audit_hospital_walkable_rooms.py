"""Read-only sampled hospital connectivity; not a substitute for player traversal."""
import collections
import json
import math
import sys
import traceback
import unreal

sys.path.insert(0, r"F:\Carnival\Scripts")
from industrial_hospital_route_config import MAIN_MAP, OUT, HOSPITAL_YAW, hospital_level_transform

report = {"success":False,"errors":[],"step_cm":100,"sampled_floor_z":80,
          "scope":"ground-floor capsule connectivity at 1 m spacing"}
origin = hospital_level_transform()
angle = math.radians(HOSPITAL_YAW)
def wp(x,y,z):
    return unreal.Vector(origin[0]+x*math.cos(angle)-y*math.sin(angle),
                         origin[1]+x*math.sin(angle)+y*math.cos(angle),origin[2]+z)
def hit(value):
    data = value.to_tuple() if value else None
    return data if data and data[0] else None
def blocked(a,b):
    h = hit(unreal.SystemLibrary.capsule_trace_single(world,a,b,42,96,
        unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True))
    if h and not (h[7].z > .707 and h[5].z < min(a.z,b.z)-60):
        return h[9].get_actor_label() if h[9] else "unknown"
    return None

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
    if not world:
        raise RuntimeError("Connected hospital world failed to load")
    nodes, blocked_counts = {}, collections.Counter()
    for x in range(1000,12001,100):
        for y in range(-7200,1601,100):
            h = hit(unreal.SystemLibrary.line_trace_single(world,wp(x,y,140),wp(x,y,0),
                unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True))
            if not h or abs(h[5].z-origin[2]-80)>20 or h[7].z<.707:
                continue
            p = wp(x,y,h[5].z-origin[2]+99)
            obstruction = blocked(p,p+unreal.Vector(1,0,0))
            if obstruction:
                blocked_counts[obstruction] += 1
            else:
                nodes[(x,y)] = p
    adjacency = {key:[] for key in nodes}
    edge_blockers = collections.Counter()
    for key,p in nodes.items():
        for dx,dy in ((100,0),(0,100)):
            other = (key[0]+dx,key[1]+dy)
            if other not in nodes:
                continue
            obstruction = blocked(p,nodes[other])
            if obstruction:
                edge_blockers[obstruction] += 1
            else:
                adjacency[key].append(other)
                adjacency[other].append(key)
    remaining, components = set(nodes), []
    while remaining:
        seed = min(remaining)
        queue, component = collections.deque([seed]), []
        remaining.remove(seed)
        while queue:
            key = queue.popleft()
            component.append(key)
            for other in adjacency[key]:
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
        components.append(component)
    components.sort(key=len,reverse=True)
    entrance = min(nodes,key=lambda p:math.dist(p,(5200,-200))) if nodes else None
    report.update(success=True,free_nodes=len(nodes),entrance_seed=entrance,
        entrance_component=next((i for i,c in enumerate(components) if entrance in c),None),
        components=[{"count":len(c),"nodes":c} for c in components],
        blocked_samples=blocked_counts.most_common(),blocked_edges=edge_blockers.most_common())
except Exception:
    report["errors"].append(traceback.format_exc())
(OUT / "Hospital_Room_Connectivity.json").write_text(json.dumps(report,indent=2))
