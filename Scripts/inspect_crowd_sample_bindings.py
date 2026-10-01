import json
from pathlib import Path
import unreal

sample = unreal.CarnivalCrowdEntitySample()
report = {'names': [name for name in dir(sample) if not name.startswith('_')], 'properties': {}}
for name in ('bInAvoidanceGrid', 'bSteeringFallingBehind', 'AgentRadius', 'MovementAction'):
    try:
        report['properties'][name] = sample.get_editor_property(name)
    except Exception as error:
        report['properties'][name] = str(error)
path = Path(unreal.Paths.project_dir()) / 'Saved/CrowdAcceptance/SampleBindings_20260930.json'
path.write_text(json.dumps(report, indent=2))
unreal.SystemLibrary.quit_editor()
