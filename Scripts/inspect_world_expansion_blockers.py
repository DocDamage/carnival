import json,math
from pathlib import Path
import unreal
ROOT=Path(r"F:\\Carnival")
MAP="/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
TARGETS={"mansion_start":(-69966.343,-85850.278,650.0),"lab_stuck":(-35908.795,-18985.184,716.906)}
OUT=ROOT/"Saved/WorldExpansion/Blocker_Inspection.json"
world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world: raise RuntimeError("Could not load Carnival map")
rows=[]
actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
for key,target in TARGETS.items():
    t=unreal.Vector(*target); near=[]
    for actor in actors:
        try:
            c,e=actor.get_actor_bounds(False,True)
            dx=max(0.,abs(c.x-t.x)-e.x); dy=max(0.,abs(c.y-t.y)-e.y); dz=max(0.,abs(c.z-t.z)-e.z)
            d=math.sqrt(dx*dx+dy*dy+dz*dz)
            if d>650: continue
            row={"name":actor.get_name(),"label":actor.get_actor_label(),"class":actor.get_class().get_name(),"distance_aabb_cm":d,"location":actor.get_actor_location().to_tuple(),"bounds_center":c.to_tuple(),"bounds_extent":e.to_tuple()}
            comp=actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp:
                m=comp.get_editor_property("static_mesh"); row["mesh"]=m.get_path_name() if m else None
                row["collision_profile"]=str(comp.get_editor_property("collision_profile_name")); row["collision_enabled"]=str(comp.get_editor_property("collision_enabled"))
            near.append(row)
        except Exception: pass
    rows.append({"target_name":key,"target":target,"actors":sorted(near,key=lambda x:x["distance_aabb_cm"])})
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps({"actor_count":len(actors),"targets":rows},indent=2),encoding="utf-8")
unreal.SystemLibrary.quit_editor()
