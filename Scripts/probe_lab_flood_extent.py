"""Read-only: Lab A anchor flood extent vs the PIE-walked path, with located frontier rejections."""
import json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
src=(ROOT/'Scripts/find_campaign_station_sites.py').read_text()
src=src[:src.index('\ntry:\n before=')].replace("OUT.mkdir(parents=True,exist_ok=False)","")
# Record where each frontier rejection happens.
src=src.replace("FRONTIER['no_floor']+=1","FRONTIER['no_floor']+=1;LOC.append(('no_floor',n,round(p.z-98)))")
src=src.replace("FRONTIER['rise_or_drop']+=1","FRONTIER['rise_or_drop']+=1;LOC.append(('rise',n,round(g.z),round(p.z-98)))")
src=src.replace("FRONTIER['standing:'+name(h)]+=1","FRONTIER['standing:'+name(h)]+=1;LOC.append(('standing',n,name(h)))")
src=src.replace("if h:FRONTIER['body:'+name(h)]+=1","if h:FRONTIER['body:'+name(h)]+=1;LOC.append(('body',(round(b.x),round(b.y)),name(h)))")
src=src.replace("FRONTIER['floor_gap']+=1","FRONTIER['floor_gap']+=1;LOC.append(('floor_gap',(round(b.x),round(b.y))))")
g={'LOC':[]};exec(compile(src,'finder_defs','exec'),g)
walk=[s['loc'] for s in json.loads((ROOT/'Saved/CampaignAcceptance/LabGateWalk3_20260930/index.json').read_text())['samples']]
R={'success':False,'errors':[]}
try:
 g['world']=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 g['WALK_IGNORE'].extend(a for a in acts if a.get_actor_label().startswith('BP_MGate01'))
 nodes,start=g['flood']((-41000,-8000,600),4000,50)
 R['start']=start;R['count']=len(nodes)
 xs=[k[0] for k in nodes];ys=[k[1] for k in nodes]
 R['bbox']=[min(xs),min(ys),max(xs),max(ys)]
 R['walk_nearest']=[[p[:2],round(min(math.dist(k,p[:2]) for k in nodes))] for p in walk]
 near=[l for l in g['LOC'] if min(math.dist(l[1],p[:2]) for p in walk)<250]
 R['frontier_near_walk']=near[:80]
 R['nodes']=sorted(nodes)
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(ROOT/'Saved/CampaignAcceptance/LabFloodExtent50_20260930.json').write_text(json.dumps(R,indent=1,default=str))
