"""Render the fitted clip on the saved Manny mesh in the shared inspection stage."""
from pathlib import Path
import runpy

PREVIEW_CONFIG={
    'rider_position':(0,0,98.195294),
    'clip':'/Game/Carnival/Vehicles/Motorcycle/Fitted/Bike_Fitted_Idle',
    'show_rider':True,
    'shots':[('RiderFitted_Front',(350,-480,220),(0,0,80)),
             ('RiderFitted_Rear',(-350,420,180),(0,0,80)),
             ('RiderFitted_Side',(0,-420,140),(0,0,85))],
    'report':'RiderFitted_Capture_Report.json',
    'scope':'Fitted idle frozen at 0.75 seconds on saved rider mesh and seat; runtime montage verified separately.'}
runpy.run_path(str(Path(__file__).with_name('preview_motorcycle_assembly.py')),
               init_globals={'PREVIEW_CONFIG':PREVIEW_CONFIG})
