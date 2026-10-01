"""Read-only: every surface under a few dock/river points with class, level and in-game visibility."""
import json,unreal
V=unreal.Vector
w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
R={}
for name,(x,y) in {'north_berth':(-49000,-58200),'north_open':(-52000,-60000),'river_mid':(-30000,-50000),'carnival_side':(-10000,-40000)}.items():
 out=[]
 for h in unreal.SystemLibrary.line_trace_multi(w,V(x,y,4000),V(x,y,-6000),unreal.TraceTypeQuery.ECC_VISIBILITY,True,[],unreal.DrawDebugTrace.NONE,True) or []:
  t=h.to_tuple();a=t[9]
  out.append({'z':round(t[5].z),'label':a.get_actor_label() if a else None,'class':a.get_class().get_name() if a else None,'level':a.get_level().get_outermost().get_name().split('/')[-1] if a else None,'hidden_in_game':a.get_editor_property('hidden') if a else None})
 R[name]=out
levels={}
for ls in unreal.EditorLevelUtils.get_levels(w):
 pass
ws=w.get_streaming_levels() if hasattr(w,'get_streaming_levels') else []
R['streaming']=[{'pkg':str(s.get_world_asset_package_name()).split('/')[-1],'visible':s.get_should_be_visible_flag() if hasattr(s,'get_should_be_visible_flag') else None,'initially_loaded':s.get_editor_property('initially_loaded') if hasattr(s,'get_editor_property') else None,'initially_visible':s.get_editor_property('initially_visible') if hasattr(s,'get_editor_property') else None,'class':s.get_class().get_name()} for s in ws]
open(r'F:\Carnival\Saved\WorldExpansion\DockGroundLayers_20261001.json','w').write(json.dumps(R,indent=1,default=str))
