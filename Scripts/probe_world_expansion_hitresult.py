import json
from pathlib import Path
import unreal
ROOT=Path(r"F:\Carnival"); out=ROOT/"Saved/WorldExpansion/Route_Surface_Probe_API.json"
world=unreal.EditorLoadingAndSavingUtils.load_map("/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival")
pts=[("lab_gate",-30000,-25000,600),("lab_stuck",-35908.8,-18985.2,600),("lab_door",-41000,-8000,600),("mansion",-69966.343,-85850.278,500),("mansion_outer",-66000,-78000,540),("route_east",70000,15000,600)]
data=[]
for name,x,y,z in pts:
 h=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,5000),unreal.Vector(x,y,-5000),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE)
 data.append({"name":name,"route_z":z,"hit_dict":{k:repr(v) for k,v in h.to_dict().items()},"hit_export":h.export_text()})
out.write_text(json.dumps(data,indent=2,default=str),encoding="utf-8")
unreal.SystemLibrary.quit_editor()
