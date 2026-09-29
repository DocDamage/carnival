"""Measure the supporting ankle against its authored peg during staged exits."""
import json
import math
from pathlib import Path
root=Path(r'F:\Carnival\Saved\DirtBike')
data=json.loads((root/'Transition_Leg_Samples.json').read_text())
report={}
for name,frames in data.items():
    if 'Staged_' not in name: continue
    left=name.endswith('Left'); bone='foot_l' if left else 'foot_r'
    target=(-8,-30 if left else 30,46)
    samples=[]
    for frame in frames:
        # Fitted source keeps the supporting foot at the peg in this phase.
        if .3<=frame['fraction']<=.65:
            point=frame['bones'][bone]
            error=math.dist(point,target)
            samples.append({'fraction':frame['fraction'],'ankle':point,'peg_error_cm':error})
    worst=max(samples,key=lambda s:s['peg_error_cm'])
    report[name]={'max_peg_error_cm':worst['peg_error_cm'],'worst_sample':worst,
                  'contact_within_2cm':worst['peg_error_cm']<=2.}
    print(name,report[name])
(root/'Staged_Dismount_Contact_Audit.json').write_text(json.dumps(report,indent=2))
