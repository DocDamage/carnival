"""Read-only: shortest flood-graph paths from region anchors to the repaired stations' stand nodes."""
import collections,json,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
src=(ROOT/'Scripts/find_campaign_station_sites.py').read_text()
src=src[:src.index('\ntry:\n before=')].replace("OUT.mkdir(parents=True,exist_ok=False)","")
g={};exec(compile(src,'finder_defs','exec'),g)
sites={r['station']:r for r in json.loads((ROOT/'Saved/CampaignAcceptance/StationSites14_20260930/index.json').read_text())['stations']}
R={'success':False,'errors':[],'paths':[]}
def neighbours(k,nodes,step):
 for dx in (-step,0,step):
  for dy in (-step,0,step):
   n=(k[0]+dx,k[1]+dy)
   if (dx or dy) and n in nodes:yield n
try:
 g['world']=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 g['WALK_IGNORE'].extend(a for a in acts if a.get_actor_label().startswith('BP_MGate01'))
 for label,seed,box,step,targets in [('lab',(-41000,-8000,600),6500,50,['lab_a_calibration','lab_b_chart','lab_b_remote']),
                                    ('prison',(-30000,-25000,600),11000,100,['prison_archive'])]:
  nodes,start=g['flood'](seed,box,step)
  # The flood only adds edges that passed the walk test, so recompute edges with edge_ok for the path.
  for st in targets:
   goal=tuple(sites[st]['controls'][0]['stand_node'])
   prev={start:None};q=collections.deque([start])
   while q:
    k=q.popleft()
    if k==goal:break
    for n in neighbours(k,nodes,step):
     if n in prev:continue
     if not g['edge_ok'](nodes[k],nodes[n]):continue
     prev[n]=k;q.append(n)
   if goal not in prev:R['paths'].append({'station':st,'found':False});continue
   path=[];k=goal
   while k:path.append(k);k=prev[k]
   path.reverse()
   pts=[list(nodes[k].to_tuple()) for k in path]
   R['paths'].append({'station':st,'found':True,'nodes':len(path),'length_m':round(sum(math.dist(pts[i][:2],pts[i+1][:2]) for i in range(len(pts)-1))/100,1),
    'waypoints':[pts[i] for i in range(0,len(pts),3)]+[pts[-1]],'start':pts[0]})
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(ROOT/'Saved/CampaignAcceptance/StationWalkPaths_20260930.json').write_text(json.dumps(R,indent=1,default=str))
