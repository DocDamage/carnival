"""Inspect the fitted left mount at start, step-over and seated endpoint."""
from pathlib import Path
import runpy

config={
    'rider_position':(0,0,98.195294),
    'clip':'/Game/Carnival/Vehicles/Motorcycle/Fitted/Bike_Fitted_Mount_Left',
    'time':0., 'times':[0.,.6666667,1.3333334,.6666667,.75,.75],
    'clips':['/Game/Carnival/Vehicles/Motorcycle/Fitted/Bike_Fitted_'+name for name in
             ['Mount_Left','Mount_Left','Mount_Left','Mount_Right','Dismount_Left','Dismount_Right']],
    'show_rider':True,
    'shots':[(name,(260,side*420,210),(0,side*30,85)) for name,side in
             [('MountFitted_Start',-1),('MountFitted_StepOver',-1),('MountFitted_Seated',-1),
              ('MountRightFitted_StepOver',1),('DismountLeftFitted_StepOver',-1),('DismountRightFitted_StepOver',1)]],
    'report':'MountFitted_Capture_Report.json',
    'scope':'Frozen samples of candidate fitted left mount; not installed or runtime transition acceptance.'}
runpy.run_path(str(Path(__file__).with_name('preview_motorcycle_assembly.py')),
              init_globals={'PREVIEW_CONFIG':config})
