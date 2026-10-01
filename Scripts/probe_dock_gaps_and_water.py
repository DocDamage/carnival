"""Read-only: what lies in the two dock gaps (East Dock quay -> loading fingers, North Dock End Platform ->
Bent Quay), and where the visible sea/river water surfaces are (for swim volumes). No saves."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/WorldExpansion/DockGapsWater_20261001.json'
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
R={'errors':[],'gaps':{},'water':[],'dock_actors':[]}
GAPS={'east':(66000,74000,18400,23000,250),'north':(-58000,-52000,-48400,-44600,200)}
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 for name,(x0,x1,y0,y1,st) in GAPS.items():
  rows=[]
  for y in range(y0,y1+1,st):
   row=[]
   for x in range(x0,x1+1,st):
    hs=unreal.SystemLibrary.line_trace_multi(world,V(x,y,2000),V(x,y,-2000),TQ,False,[],N,True) or []
    row.append([(h.to_tuple()[9].get_actor_label() if h.to_tuple()[9] else '?',round(h.to_tuple()[5].z)) for h in hs][:3])
   rows.append({'y':y,'cells':row})
  R['gaps'][name]={'x':list(range(x0,x1+1,st)),'rows':rows}
 for a in acts:
  lvl=a.get_level().get_outermost().get_name().split('/')[-1]
  cls=a.get_class().get_name();lab=a.get_actor_label()
  o,e=a.get_actor_bounds(False)
  mats=[]
  for c in a.get_components_by_class(unreal.PrimitiveComponent):
   try:
    for i in range(c.get_num_materials()):
     m=c.get_material(i)
     if m:mats.append(m.get_name())
   except Exception:pass
  if 'Water' in cls or any(k in (' '.join(mats)+' '+lab).lower() for k in ('water','ocean','sea_','river','lake')):
   R['water'].append({'label':lab,'class':cls,'level':lvl,'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()],'materials':sorted(set(mats))[:6]})
  if lab.startswith(('EastDock_','NorthDock_')) or 'Dock' in lvl:
   R['dock_actors'].append({'label':lab,'class':cls,'level':lvl,'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]})
except Exception:R['errors'].append(traceback.format_exc())
OUT.write_text(json.dumps(R,indent=1))
