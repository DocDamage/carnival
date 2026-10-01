"""Make the North Dock boat ramp's top flush with the pier.

BoardingDeck_0 (21-degree ramp) was centred so its top end stood 37 cm above the pier
(672 vs 635) with a slanted end face; the walk to the boat now stalls there. The lower end
(surface -210, meeting BoardingDeck_1) is kept; the ramp is shortened from the top so its upper
end surface is 635 at the pier's end (y -55000). Only the North Docks level is saved (backed up).
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_CarnivalWorldExpansion_DocksNorth_Layout'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout.umap'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/WaterVehicleAcceptance/RampLipFix_20261001';OUT.mkdir(parents=True,exist_ok=False)
PIER_TOP=635.0;R={'success':False,'errors':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 R.update(level_sha256_before=sha(LEVEL_FILE),map_sha256_before=sha(MAPFILE));shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_ramp_lip_fix.umap'))
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 deck=next(a for a in EA.get_all_level_actors() if a.get_actor_label()=='Boat_NorthDock_Inflatable_BoardingDeck_0')
 c=deck.get_actor_location();r=deck.get_actor_rotation();s=deck.get_actor_scale3d()
 assert abs(r.yaw+90)<.01 and abs(r.pitch+21.011)<.05,'unexpected ramp orientation'
 th=math.radians(-r.pitch);half=s.x*50;half_t=s.z*50
 surf_off=half_t*math.cos(th)
 low_y=c.y-half*math.cos(th);low_surf=c.z+surf_off-half*math.sin(th)   # forward is -y (yaw -90)
 run=(PIER_TOP-low_surf)/math.tan(th);new_len=run/math.cos(th)
 new_cy=low_y+run/2;new_cz=(PIER_TOP+low_surf)/2-surf_off
 R['before']={'center':list(c.to_tuple()),'scale_x':s.x,'top_y':c.y+half*math.cos(th),'top_surface_z':c.z+surf_off+half*math.sin(th)}
 deck.modify();deck.set_actor_location(unreal.Vector(c.x,new_cy,new_cz),False,True);deck.set_actor_scale3d(unreal.Vector(new_len/100,s.y,s.z))
 R['after']={'center':[c.x,new_cy,new_cz],'scale_x':new_len/100,'top_y':low_y+run,'top_surface_z':PIER_TOP,'low_end_y':low_y,'low_surface_z':low_surf}
 assert unreal.EditorLoadingAndSavingUtils.save_packages([deck.get_outermost()],False)
 R.update(level_sha256_after=sha(LEVEL_FILE),map_sha256_after=sha(MAPFILE));assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
