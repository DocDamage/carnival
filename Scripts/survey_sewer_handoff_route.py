"""Find a capsule-clear candidate between the actual R10 landing and R11.

Read-only collision graph with measured edge checks. A candidate is never
player acceptance; the production pawn must walk it out and continuously back.
"""
import collections,hashlib,heapq,json,math,os,traceback
from pathlib import Path
import unreal

ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion'
REPORT={'success':False,'route_found':False,'errors':[],'grid_step_cm':100,
    'capsule_radius_cm':42,'capsule_half_height_cm':96,
    'route_clearance_margin_cm':12,
    'limits':'Read-only editor collision graph; requires actual pawn continuous round trip and camera/rendered review.'}
MAIN='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
fine=os.environ.get('CARNIVAL_SEWER_FINE_SURVEY')=='1'
north=os.environ.get('CARNIVAL_SEWER_NORTH_SURVEY')=='1'
start_xy=(-27000,-12659) if fine else (-27000,-12700);end_xy=(-27100,-9654)
REPORT['fine_landing_grid_step_cm']=25 if fine else None
for name in ('L_CarnivalWorldExpansion_Sewers','L_CarnivalWorldExpansion_Connections_Layout'):
    path=ROOT/'Content/Carnival/World/Levels'/(name+'.umap')
    REPORT.setdefault('source_hashes',{})[name]=hashlib.sha256(path.read_bytes()).hexdigest()

def hit(value):
    h=value.to_tuple() if value else None
    return h if h and h[0] else None

def floor(x,y):
    h=hit(unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,-1700),unreal.Vector(x,y,-2050),
        unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignored,unreal.DrawDebugTrace.NONE,True))
    if not h or h[1] or h[7].z<.7: return None
    floor_normals[(round(x),round(y))]=float(h[7].z)
    return h[5]

def grounded_center(point):
    # A grounded capsule's curved bottom supports above a sloping plane.
    # R*(sec(slope)-1) is the extra center height relative to a flat floor.
    # Account for the padded 54 cm radius rather than falsely reporting
    # initial overlap with the walkable 19-degree authored ramp itself.
    nz=floor_normals[(round(point.x),round(point.y))]
    return point+unreal.Vector(0,0,99+54*(1/nz-1))

def obstruction(a,b):
    skipped=[]
    for attempt in range(12):
        h=hit(unreal.SystemLibrary.capsule_trace_single(world,a,b,54,96,
            unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignored+skipped,unreal.DrawDebugTrace.NONE,True))
        actor=h[9] if h else None
        label=actor.get_actor_label() if actor else ''
        owned_ramp=actor and label in ('SewerStair_PublicFloorHandoff','SewerStair_PublicFloorHandoff_Lower','SewerR11_PublicFloorApproach','SewerR11_PublicFloorMouth') and 'CarnivalInteriorHandoffRepair' in [str(t) for t in actor.tags]
        if h and actor and (label=='PrisonSewer_StairTread' or owned_ramp) and h[5].z<min(a.z,b.z)-96+45:
            # The validated low riser is walkable, but it can be the first hit
            # in front of a separate ceiling/vent obstruction. Retry after
            # ignoring only this exact tread/owned low floor riser, rather than declaring the whole
            # capsule sweep clear after its first floor contact.
            skipped.append(h[9])
            REPORT['authored_stair_step_contacts']=REPORT.get('authored_stair_step_contacts',0)+1
            continue
        break
    else:return 'Unresolved repeated stair contacts'
    if h and not (not h[1] and h[7].z>.707 and h[5].z<min(a.z,b.z)-60):
        return h[9].get_path_name() if h[9] else 'unknown'
    return None

try:
    world=unreal.EditorLoadingAndSavingUtils.load_map(MAIN);assert world
    actors=list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    ignored=[a for a in actors if isinstance(a,unreal.Pawn)]
    nodes={};floor_normals={};blocked=collections.Counter();node_blockers=[]
    grid={(x,y) for x in range(-27900,-26199,100) for y in range(-12900,-9399,100)}
    if fine:
        grid.update((x,y) for x in range(-27300,-26699,25) for y in range(-12800,-11899,25))
    if north:
        assert fine,'North handoff refinement also needs the landing fine grid'
        grid.update((x,y) for x in range(-27500,-26499,25) for y in range(-10800,-9499,25))
    for x,y in sorted(grid):
            point=floor(x,y)
            if not point: continue
            center=grounded_center(point)
            blocker=obstruction(center,center+unreal.Vector(.1,0,0))
            if blocker:
                blocked[blocker]+=1
                if fine:node_blockers.append({'xy_cm':[x,y],'floor_cm':list(point.to_tuple()),'actor':blocker})
            else: nodes[(x,y)]=point
    if not nodes: raise RuntimeError('No floor/capsule positive controls in sewer corridor')
    edges={key:[] for key in nodes};edge_blockers=collections.Counter()
    for key,point in nodes.items():
        for dx,dy in (((100,0),(0,100),(25,0),(0,25)) if fine else ((100,0),(0,100))):
            other=(key[0]+dx,key[1]+dy)
            if other not in nodes or abs(point.z-nodes[other].z)>45: continue
            blocker=obstruction(grounded_center(point),grounded_center(nodes[other]))
            if blocker: edge_blockers[blocker]+=1
            else: edges[key].append(other);edges[other].append(key)
    start=min(nodes,key=lambda p:math.dist(p,start_xy));finish=min(nodes,key=lambda p:math.dist(p,end_xy))
    REPORT.update(nodes=[{'xy_cm':list(k),'floor_cm':list(v.to_tuple()),'edges':[list(x) for x in edges[k]]} for k,v in nodes.items()],
        start_seed_xy=start,end_seed_xy=finish,start_seed_error_cm=math.dist(start,start_xy),
        end_seed_error_cm=math.dist(finish,end_xy),blocked_nodes=blocked.most_common(),blocked_edges=edge_blockers.most_common())
    if fine:
        REPORT['blocked_node_points']=node_blockers
        relevant={row['actor'] for row in node_blockers if math.dist(row['xy_cm'],start_xy)<500 or
                  north and math.dist(row['xy_cm'],end_xy)<1100}
        REPORT['landing_obstruction_inventory']=[]
        for actor in actors:
            if actor.get_path_name() not in relevant:continue
            center,extent=actor.get_actor_bounds(False,True)
            component=actor.get_component_by_class(unreal.StaticMeshComponent)
            mesh=component.get_editor_property('static_mesh') if component else None
            REPORT['landing_obstruction_inventory'].append({'actor':actor.get_path_name(),
                'label':actor.get_actor_label(),'location_cm':actor.get_actor_location().to_tuple(),
                'rotation':str(actor.get_actor_rotation()),'scale':actor.get_actor_scale3d().to_tuple(),
                'bounds_center_cm':center.to_tuple(),'bounds_extent_cm':extent.to_tuple(),
                'mesh':mesh.get_path_name() if mesh else None})
    if REPORT['start_seed_error_cm']>80 or REPORT['end_seed_error_cm']>80:
        REPORT['route_failure']='No capsule-clear node close enough to a real handoff'
    else:
        frontier=[(math.dist(start,finish),0,start)];costs={start:0};parents={}
        while frontier:
            _,cost,key=heapq.heappop(frontier)
            if key==finish:
                path=[key]
                while key!=start: key=parents[key];path.append(key)
                path.reverse();REPORT['candidate_floor_points_cm']=[list(nodes[k].to_tuple()) for k in path]
                REPORT['route_found']=True;break
            if cost!=costs[key]: continue
            for other in edges[key]:
                new_cost=cost+unreal.Vector.distance(nodes[key],nodes[other])
                if new_cost<costs.get(other,float('inf')):
                    costs[other]=new_cost;parents[other]=key
                    heapq.heappush(frontier,(new_cost+math.dist(other,finish),new_cost,other))
        if not REPORT['route_found']:
            REPORT['route_failure']='No measured capsule-clear edge path joins the handoffs'
            closest=min(costs,key=lambda p:math.dist(p,finish))
            partial=[closest];key=closest
            while key!=start:key=parents[key];partial.append(key)
            partial.reverse()
            REPORT['partial_floor_points_cm']=[list(nodes[k].to_tuple()) for k in partial]
            REPORT['partial_remaining_handoff_gap_cm']=math.dist(closest,finish)
            REPORT['partial_scope']='Reachable lower corridor only; full R11 connection remains failed. Requires real pawn acceptance.'
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc())
(OUT/('Sewer_Handoff_Fine_Candidate.json' if fine else 'Sewer_Handoff_Candidate.json')).write_text(json.dumps(REPORT,indent=2))
