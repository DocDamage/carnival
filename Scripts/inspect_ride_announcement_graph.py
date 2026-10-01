"""Inspect the imported ride parent's actual announcement execution graph."""
import json
from pathlib import Path
import unreal

path = '/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/Structure/BP_Rides_Parent'
blueprint = unreal.load_asset(path)
assert blueprint
lines = list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(blueprint))
assert lines
out = Path(unreal.Paths.project_dir()) / 'Saved/RideDevelopment/AnnouncementParentGraph_20260930.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'asset': path, 'assets_modified': False, 'execution': lines}, indent=2))
unreal.SystemLibrary.quit_editor()
