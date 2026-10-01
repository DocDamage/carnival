import json,unreal
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
ws=world.get_world_settings();out={}
for k in ('enable_navigation_system','enable_ai_system'):
 try:out[k]=ws.get_editor_property(k)
 except Exception as e:out[k]='err '+str(e)[:80]
nav=unreal.NavigationSystemV1.get_navigation_system(world);out['nav_system']=str(nav)
if nav:
 for k in ('auto_create_navigation_data','spawn_nav_data_in_nav_bounds_level','supported_agents','data_gathering_mode','initial_building_locked','allow_client_side_navigation'):
  try:out[k]=str(nav.get_editor_property(k))[:300]
  except Exception as e:out[k]='err '+str(e)[:80]
cdo=unreal.get_default_object(unreal.NavigationSystemV1)
for k in ('auto_create_navigation_data','supported_agents','default_agent_name'):
 try:out['cdo_'+k]=str(cdo.get_editor_property(k))[:300]
 except Exception as e:out['cdo_'+k]='err '+str(e)[:80]
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\NavSettings.json','w').write(json.dumps(out,indent=1,default=str))
