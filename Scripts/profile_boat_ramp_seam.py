import json,unreal
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
V=unreal.Vector;out=[]
for y in range(-54800,-55160,-10):
 h=unreal.SystemLibrary.line_trace_single(world,V(-50300,y,900),V(-50300,y,300),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True).to_tuple()
 out.append([y,round(h[5].z,1) if h[0] else None,round(h[7].z,3) if h[0] else None,h[9].get_actor_label() if h[0] and h[9] else None])
d=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label().startswith('Boat_NorthDock_Inflatable_BoardingDeck')]
decks=[{'label':a.get_actor_label(),'loc':list(a.get_actor_location().to_tuple()),'rot':list(a.get_actor_rotation().to_tuple()),'scale':list(a.get_actor_scale3d().to_tuple())} for a in d]
open(r'F:\Carnival\Saved\WorldExpansion\WaterVehicleAcceptance\RampSeamProfile_20261001.json','w').write(json.dumps({'profile':out,'decks':decks},indent=1))
