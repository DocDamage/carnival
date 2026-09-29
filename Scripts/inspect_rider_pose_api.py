"""Read installed animation-authoring API and current clip pose for fitting."""
import json
from pathlib import Path
import unreal
result = {}
for name in ['AnimPoseExtensions','AnimPoseEvaluationOptions','AnimDataController','AnimPose','AnimationLibrary','AnimationBlueprintLibrary']:
    cls = getattr(unreal, name, None)
    result[name] = {'doc':str(getattr(cls,'__doc__','')), 'methods':{
        method:str(getattr(cls,method).__doc__) for method in dir(cls or object)
        if not method.startswith('_') and any(s in method for s in ('pose','bone','track','key','frame','sequence'))}}
Path(r'F:\Carnival\Saved\DirtBike\Pose_Authoring_API.json').write_text(json.dumps(result,indent=2))
