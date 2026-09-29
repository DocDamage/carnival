import json, math
from pathlib import Path
import unreal
ROOT=Path(r"F:\Carnival")
PACKAGE="/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout"
OUT=ROOT/"Saved/WorldExpansion"
REGION_JSON=OUT/"Region_Authoring.json"
MANSION_JSON=ROOT/"Saved/MansionConnection/Route_Layout.json"
report_path=OUT/"Route_Alignment_Repair.json"

def v(p): return unreal.Vector(*[float(x) for x in p])
def catmull(controls,step=700.0):
    pts=[]
    for i in range(len(controls)-1):
        p0,p1,p2,p3=controls[max(i-1,0)],controls[i],controls[i+1],controls[min(i+2,len(controls)-1)]
        n=max(2,int(math.ceil(math.dist(p1,p2)/step)))
        for j in range(n):
            t=j/float(n); t2=t*t; t3=t2*t
            pts.append(tuple(.5*(2*p1[k]+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t2+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t3) for k in range(3)))
    pts.append(tuple(controls[-1])); return pts

def set_box_actor(actor, center, size, material, rotation, label):
    component=actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_editor_property("static_mesh",unreal.load_asset("/Engine/BasicShapes/Cube"))
    if material: component.set_material(0,material)
    component.set_collision_profile_name("BlockAll")
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    actor.set_actor_location(v(center),False,True)
    actor.set_actor_rotation(unreal.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]),True)
    actor.set_actor_scale3d(v((size[0]/100.0,size[1]/100.0,size[2]/100.0)))
    actor.set_actor_label(label,True)
    tags=list(actor.get_editor_property("tags")); tag=unreal.Name("WorldExpansionGenerated")
    if tag not in tags: tags.append(tag)
    actor.set_editor_property("tags",tags)

mansion=json.loads(MANSION_JSON.read_text(encoding="utf-8"))
start=tuple(mansion["route_world"][-1])
region=json.loads(REGION_JSON.read_text(encoding="utf-8"))
connections={c["id"]:c for c in region["connections"]}
old_controls=[tuple(p) for p in (
    region.get("outer_route_spine", {}).get("controls_cm")
    or connections["R03"]["route"].get("spine_controls_cm")
    or connections["R03"]["route"].get("controls_cm", []))]
if len(old_controls) < 2:
    raise RuntimeError("No existing outer-route controls were found")
controls=[start]+old_controls[1:]
points=catmull(controls)
world=unreal.EditorLoadingAndSavingUtils.load_map(PACKAGE)
if not world: raise RuntimeError("Could not open connector level")
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
removed=[]
expected_old_segments=int(region.get("outer_route_spine", {}).get("segment_count", 0))
for actor in list(eas.get_all_level_actors()):
    try:
        if actor.get_actor_label()=="OuterRoute_Segment":
            removed.append(actor.get_path_name()); eas.destroy_actor(actor)
    except Exception: pass
if not expected_old_segments or len(removed)!=expected_old_segments:
    raise RuntimeError("Expected %d generated outer-route segments, found %d"%(expected_old_segments,len(removed)))
material=unreal.load_asset("/Game/Docks/VOL2_Powell/Materials/Instances/MI_Sand_01a")
created=0
for a,b in zip(points,points[1:]):
    dx,dy,dz=(b[i]-a[i] for i in range(3)); horiz=max(1.0,math.hypot(dx,dy))
    center=tuple((a[i]+b[i])*0.5 for i in range(3))
    size=(math.sqrt(dx*dx+dy*dy+dz*dz)+24.0,760.0,45.0)
    actor=eas.spawn_actor_from_class(unreal.StaticMeshActor,v(center),unreal.Rotator(
        pitch=math.degrees(math.atan2(dz,horiz)),
        yaw=math.degrees(math.atan2(dy,dx)),roll=0.0))
    if not actor: raise RuntimeError("Could not spawn an outer route segment")
    set_box_actor(actor,center,size,material,(math.degrees(math.atan2(dz,horiz)),math.degrees(math.atan2(dy,dx)),0.0),"OuterRoute_Segment")
    created+=1
if created!=len(points)-1: raise RuntimeError("Outer route actor count mismatch")
if not unreal.EditorLoadingAndSavingUtils.save_map(world,PACKAGE): raise RuntimeError("Could not save connector level")
# Each register row keeps the full continuous spline controls and identifies its own actual endpoint pair.
endpoint_nodes=[
 ("Mansion",0,start),
 ("DocksNorth",4,tuple(controls[4])),
 ("Prison",8,tuple(controls[8])),
 ("DocksEast",15,tuple(controls[15])),
 ("Hospital",len(controls)-1,tuple(controls[-1])),
]
edge_rows=[]
for cid,(a_name,a_i,a_pos),(b_name,b_i,b_pos) in zip(("R03","R04","R05","R06"),endpoint_nodes,endpoint_nodes[1:]):
    section=points[max(0,int((a_i/(len(controls)-1))*(len(points)-1))):min(len(points),int((b_i/(len(controls)-1))*(len(points)-1))+1)]
    segment_length=sum(math.dist(x,y) for x,y in zip(section,section[1:]))/100.0
    edge_rows.append({"id":cid,"from":a_name,"to":b_name,"type":"surface","route":{
        "name":"OuterRoute","spine_controls_cm":[list(p) for p in controls],"control_range_inclusive":[a_i,b_i],
        "length_m_estimate":segment_length,"surface_width_cm":760,"floor_thickness_cm":45},
        "endpoints":{"a":{"region":a_name,"world_cm":list(a_pos)},"b":{"region":b_name,"world_cm":list(b_pos)}}})
for row in edge_rows:
    dst=connections[row["id"]]
    dst["route"].update(row["route"])
    dst["endpoints"]=row["endpoints"]
    dst["route"].pop("controls_cm",None)
region["connections"]=[connections.get(c["id"],c) for c in region["connections"]]
region["outer_route_spine"]={"controls_cm":[list(p) for p in controls],"length_m":sum(math.dist(a,b) for a,b in zip(points,points[1:]))/100.0,"segment_count":created,"start_source":"existing Mansion driveway endpoint from Route_Layout.json","start_cm":list(start)}
REGION_JSON.write_text(json.dumps(region,indent=2),encoding="utf-8")
report={"success":True,"map":PACKAGE,"old_generated_segments_removed":len(removed),"new_generated_segments":created,"mansion_driveway_exit_cm":list(start),"route_length_m":region["outer_route_spine"]["length_m"],"endpoint_pairs":edge_rows,"visual_appearance":"same sand material and collision surface; only starting endpoint aligned"}
report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
unreal.SystemLibrary.quit_editor()
