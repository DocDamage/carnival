import json, math
from pathlib import Path
import unreal
ROOT=Path(r"F:\Carnival")
MAP="/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival"
out=ROOT/"Saved/WorldExpansion/Route_Surface_Probe.json"
data={"doc":unreal.SystemLibrary.line_trace_single.__doc__,"points":[]}
world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world: raise RuntimeError("map load failed")
for name,x,y,z in [("prison_gate",-30000,-25000,600),("lab_stuck",-35908.8,-18985.2,600),("lab_mid",-39000,-12000,600),("lab_door",-41000,-8000,600),("mansion",-69966.343,-85850.278,500),("route_1",-66000,-78000,540),("route_2",-60000,-68000,570),("route_3",-55000,-55000,600),("route_4",-35000,-30000,600),("docks_east",70000,15000,600)]:
 row={"name":name,"route_z":z}
 try:
  hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,5000),unreal.Vector(x,y,-5000),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE)
  row["hit"]=bool(hit)
  if hit:
   for prop in ("impact_point","location","normal","distance","blocking_hit"):
    try:
     v=hit.get_editor_property(prop)
     row[prop]=v.to_tuple() if hasattr(v,"to_tuple") else v
    except Exception as e: row[prop+"_err"]=repr(e)
   try: row["actor"]=hit.get_editor_property("actor").get_path_name()
   except Exception as e: row["actor_err"]=repr(e)
   try: row["component"]=hit.get_editor_property("component").get_path_name()
   except Exception as e: row["component_err"]=repr(e)
 except Exception as e: row["trace_error"]=repr(e)
 data["points"].append(row)
out.write_text(json.dumps(data,indent=2),encoding="utf-8")
unreal.SystemLibrary.quit_editor()
