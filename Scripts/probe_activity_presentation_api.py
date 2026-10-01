"""Preflight Python bindings used by the full populated visual review."""
import json
from pathlib import Path
import unreal

assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
actor=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CarnivalActivityBase,unreal.Vector())
actor.set_editor_property('activity_name','Activity_MidwayStuntRally')
component=actor.get_editor_property('prompt_text')
REPORT={'success':True,'title':actor.get_display_title(),'world_size':component.get_editor_property('world_size'),
        'hidden_in_game':component.get_editor_property('hidden_in_game'),'assets_saved':False}
assert REPORT['title']=='Midway Stunt Rally'
(Path(unreal.Paths.project_dir())/'Saved/PresentationAcceptance/ActivityPresentationApi_20260930.json').write_text(json.dumps(REPORT,indent=2))
