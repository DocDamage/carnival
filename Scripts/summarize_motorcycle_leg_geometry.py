import json
from pathlib import Path
from collections import Counter
data=json.loads(Path(r'F:\Carnival\Saved\DirtBike\Transition_Leg_Geometry.json').read_text())
for name,result in data.items():
    hits=result['centerline_intersections']
    print(name,Counter(h['leg_segment'] for h in hits))
    print('first',hits[:1],'last',hits[-1:])
    for segment in sorted({h['leg_segment'] for h in hits}):
        group=[h for h in hits if h['leg_segment']==segment]
        print(segment,round(min(h['fraction'] for h in group),3),round(max(h['fraction'] for h in group),3))
