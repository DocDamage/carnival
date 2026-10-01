"""Read-only: floor surface types of walkable nodes around the slums R07 interface."""
import collections,json,math
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
src=(ROOT/'Scripts/find_campaign_station_sites.py').read_text()
src=src[:src.index('\ntry:\n before=')].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(src,'finder_defs','exec'),g)
g['world']=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
nodes,start=g['flood']((46912,71854,73),4500)
V=unreal.Vector;cnt=collections.Counter();off=[]
for k,c in nodes.items():
 h=g['t'](unreal.SystemLibrary.line_trace_single(g['world'],c,c-V(0,0,200),g['TQ'],False,[],g['NONE'],True))
 lab=h[9].get_actor_label() if h and h[9] else '?'
 cnt[lab]+=1
 if not any(w in lab.lower() for w in g['ROUTE_FLOOR_WORDS']):off.append((round(math.dist(k,start)),k,lab))
off.sort()
(ROOT/'Saved/CampaignAcceptance/SlumsFloorTypes_20261001.json').write_text(json.dumps({'nodes':len(nodes),'floors':cnt.most_common(30),'nearest_off_route':off[:40]},indent=1))
