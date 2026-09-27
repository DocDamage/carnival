"""Attach the finished coastal approach and mansion to the current Carnival map."""
import sys,json
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import *
main=unreal.EditorLoadingAndSavingUtils.load_map(CARNIVAL)
for level in list(unreal.EditorLevelUtils.get_levels(main)):
    if any(level.get_path_name().startswith(p+'.') for p in [COAST,MANSION]):
        assert unreal.EditorLevelUtils.remove_level_from_world(level)
for path,loc,yaw in [(COAST,COAST_ORIGIN,COAST_YAW),(MANSION,world_point(MANSION_LOCAL),COAST_YAW+MANSION_LOCAL_YAW)]:
    tf=unreal.Transform(location=unreal.Vector(*loc),rotation=unreal.Rotator(pitch=0,yaw=yaw,roll=0),scale=unreal.Vector(1,1,1))
    streaming=unreal.EditorLevelUtils.add_level_to_world_with_transform(main,path,unreal.LevelStreamingAlwaysLoaded,tf)
    assert streaming,path
    streaming.set_editor_property('should_be_visible',True)
assert unreal.EditorLoadingAndSavingUtils.save_map(main,CARNIVAL)
report=json.loads((OUT/'Connection_Build.json').read_text())
report.pop('error',None);report['phase']='complete';report['main_map']=main.get_path_name()
report['levels']=[level.get_path_name() for level in unreal.EditorLevelUtils.get_levels(main)]
(OUT/'Connection_Build.json').write_text(json.dumps(report,indent=2))
unreal.log('MANSION_COAST_CONNECTION_SAVED')
