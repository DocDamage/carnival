import json
from pathlib import Path
for clip in json.loads(Path(r'F:\Carnival\Saved\DirtBike\Transition_Fitting.json').read_text()):
    print(clip['asset'], 'max grip reach shortfall',max(s['unreachable_cm'] for s in clip['contact_samples']),
          'max seated error',max(clip['seated_joint_errors_cm'].values()))
    print('worst approach',max(clip['contact_samples'],key=lambda s:s['unreachable_cm']))
    if clip.get('leg_reach'): print('worst leg reach',max(clip['leg_reach'],key=lambda s:s['shortfall_cm']))
