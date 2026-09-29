"""Read-only native graph inspection, including actual links around activation."""
import json
from pathlib import Path
import unreal

assets=(
    '/Game/Carnival/Rides/BP_HotAirBalloon_Carnival',
    '/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/BP_HotairBalloon_Ride_01a',
    '/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/Structure/BP_Rides_Parent',
)
report={}
for path in assets:
    bp=unreal.load_asset(path)
    report[path]=list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(bp)) if bp else ['Missing asset']
out=Path(unreal.Paths.project_dir())/'Saved/RideDevelopment/BalloonExecution.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2))
unreal.SystemLibrary.quit_editor()
