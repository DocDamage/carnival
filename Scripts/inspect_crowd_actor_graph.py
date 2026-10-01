"""Read the stock crowd actor's execution graph; never modify plugin content."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
asset = unreal.load_asset('/MetaHumanCrowd/BP_CrowdActor')
assert asset
REPORT = {'success': True, 'errors': [], 'asset': asset.get_path_name(), 'assets_modified': False,
          'execution': list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(asset))}
assert REPORT['execution']
out = ROOT/'Saved/CrowdAcceptance/CrowdActorGraph_20260930.json'
out.write_text(json.dumps(REPORT, indent=2))
