"""Extend the concrete hover plan only after the dense basin survey passes.

Offline only. Does not edit levels. The authoring and real-pawn lifecycle must
still run after this plan is created. Never carve a terrain asset for the berth.
"""
import hashlib,json,math
from pathlib import Path
ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion/WaterVehicleAcceptance'
path=OUT/'DockWaterBerth.json'; survey=json.loads(path.read_text())
if not survey.get('success'): raise RuntimeError('Dense water survey failed')
rows={tuple(s['query_xy_cm']):s for s in survey['samples']}
minimum=(-49400,-59000); maximum=(-48600,-56800)
checked=[]
for x in range(minimum[0],maximum[0]+1,100):
    for y in range(minimum[1],maximum[1]+1,100):
        s=rows.get((x,y))
        if not s or not s.get('query_succeeded') or not s.get('same_body_overlap'):
            raise RuntimeError(f'No actual water membership at {(x,y)}')
        ground=s.get('ground')
        if not ground or ground['initial_overlap'] or ground['depth_below_surface_cm']<200:
            raise RuntimeError(f'Insufficient measured keel depth at {(x,y)}: {ground}')
        if abs(s['surface_cm'][2]+240)>.1: raise RuntimeError('Region water plane is not flat at surveyed Z-240')
        checked.append(ground['depth_below_surface_cm'])

plan_path=OUT/'PlacementPlan.json'; plan=json.loads(plan_path.read_text())
plan['berth_survey_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
label='Boat_NorthDock_Inflatable'
plan['entries']=[e for e in plan['entries'] if e['label']!=label]
run=2300.; rise=(635-(-210))/2200*2300
top_start=-210+rise; length=math.hypot(run,rise); pitch=-math.degrees(math.atan2(rise,run))
center_top=(top_start-210)/2; center_z=center_top-17.5*math.cos(math.radians(pitch))
def ramp_floor(y): return 635+(y+55000)*(845/2200)
plan['entries'].append({
    'kind':'boat','label':label,'map':'/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout',
    'mesh':'/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Inflatable_Boat',
    'location_local_cm':[6000,-2200,-840],'yaw_local_deg':-90,
    'collision_half_extent_cm':[250,115,90],'mount_half_extent_cm':[320,260,200],
    'driver_relative_offset_cm':[0,0,140],'water_plane_world_z':-240,
    'navigable_water_min_world_cm':list(minimum),'navigable_water_max_world_cm':list(maximum),
    'minimum_keel_clearance_cm':25,
    'water_survey_evidence':{'file':path.name,'sample_count':len(checked),'minimum_terrain_depth_cm':min(checked),'water_plane_z_cm':-240,'grid_spacing_cm':100,'same_body_overlap_required':True},
    'boarding_survey_evidence':{'existing':'NorthDock_Side_Pier','floor_z_cm':635,'extension':'New 21 degree project-owned ramp to a low deck 30 cm above measured water; acceptance pending.'},
    'boarding_decks':[
        {'center_local_cm':[4700,-1050,center_z-600],'size_cm':[length,400,35],'rotation_deg':[pitch,-90,0],'material_from_actor':'NorthDock_Side_Pier'},
        {'center_local_cm':[5150,-2200,-827.5],'size_cm':[1300,400,35],'rotation_deg':[0,0,0],'material_from_actor':'NorthDock_Side_Pier'},
    ],
    'approach_world_cm':[[-50300,-54500,635],[-50300,-54800,635],[-50300,-55050,ramp_floor(-55050)],[-50300,-55800,ramp_floor(-55800)],[-50300,-56600,ramp_floor(-56600)],[-50300,-57200,-210],[-49800,-57200,-210],[-49260,-57200,-210]],
    'drive_lane_survey_evidence':{'file':path.name,'grid_spacing_cm':100,'sample_count':len(checked),'minimum_terrain_depth_cm':min(checked)},
    'drive_distance_cm':1200,'drive_lane_half_width_cm':100,'drive_max_height_delta_cm':60,
    'activity_location_local_cm':[5350,-2200,-780],'activity_name':'North Dock Boat Handling',
    'activity_description':'Board the inflatable boat, follow the channel marker, then reverse to the low berth and unload onto the dock.',
    'checkpoints_world_cm':[[-49000,-58400,-240],[-49000,-57200,-240]],'checkpoint_radius_cm':200,'time_limit':120,
    'visual_acceptance':'Pending rendered boarding ramp, rider seated pose, visible hull, water and camera review.'
})
plan_path.write_text(json.dumps(plan,indent=2))
print(f'Prepared project boat berth after {len(checked)} valid water samples; minimum actual depth {min(checked):.1f} cm. Authoring/PIE still required.')
