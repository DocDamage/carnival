"""Read-only reachability audit of one region (env CARNIVAL_REGION).

Maps every standing-clear walkable floor layer in the region box (stacked traces, so upper floors
count), links neighbouring cells with character-realistic directed moves (step <= 45 cm with body
clearance and floor continuity; drops <= 400 cm with a clear walk-off and fall), then from the
entrance computes:
  reachable  - cells the player can get to;
  traps      - reachable cells from which the entrance cannot be reached again;
  unreachable- walkable cells never reached (sealed rooms or unused spaces).
Traps and unreachable cells are clustered and reported with their floor actors. Nothing is saved.
"""
import collections,json,math,os,time,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
REGIONS={
 'mansion':dict(entrance=(-70105,-86766,820),center=(-70500,-88000),half=2600,z=(500,3200),step=50),
 'hospital':dict(entrance=(97300,130100,645),center=(96500,128500),half=6500,z=(450,2600),step=100),
 'prison':dict(entrance=(-30158,-24842,600),center=(-28000,-30000),half=7000,z=(300,3500),step=100),
 'labs':dict(entrance=(-41000,-8000,620),center=(-42400,-6000),half=3200,z=(450,1400),step=50),
 'sewers':dict(entrance=(-27050,-11100,-1780),center=(-27000,-14000),half=5500,z=(-2600,-300),step=50),
 'atlantis_shipwreck':dict(entrance=(-13500,-11000,-1750),center=(-13000,-10500),half=8500,z=(-2400,-500),step=100),
 'slums':dict(entrance=(46912,71854,90),center=(44500,61000),half=12000,z=(0,3000),step=100),
 'docks_north':dict(entrance=(-55400,-54800,600),center=(-56000,-51500),half=8000,z=(-300,1200),step=100),
 'hospital_fine':dict(entrance=(97283,130125,643),center=(97900,127600),half=3700,z=(450,2700),step=50),
 'hospital_entrance':dict(entrance=(95552,128289,656),center=(96200,128900),half=2200,z=(450,1300),step=50),
 'atlantis_fine':dict(entrance=(-13500,-11000,-1750),center=(-13000,-10800),half=8500,z=(-2400,-1200),step=50),
 'docks_east':dict(entrance=(70300,17200,650),center=(70300,21000),half=11000,z=(200,1200),step=100),
}
NAME=os.environ.get('CARNIVAL_REGION','labs');SPEC=REGIONS[NAME]
OUT=ROOT/'Saved/WorldExpansion/Reachability'/(NAME+os.environ.get('CARNIVAL_AUDIT_SUFFIX','_v4_20261001'));OUT.mkdir(parents=True,exist_ok=False)
STEP_UP=45.0;MAX_DROP=400.0;R={'success':False,'errors':[],'region':NAME,'spec':SPEC}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def label(h):return h[9].get_actor_label() if h and h[9] else ''
try:
 t0=time.time()
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 # Doors that open in play are passable: the lab gate (verified in PIE) and the mansion BP_Door set.
 ignore=[a for a in acts if a.get_actor_label().startswith(('BP_MGate01','BP_Door'))]
 R['passable_doors']=sorted({a.get_actor_label() for a in ignore})
 anchors=[x['location'] for x in json.loads((ROOT/'Saved/WorldExpansion/RouteAnchors_20261001/index.json').read_text())['anchors']]
 stands=[]
 for nm in ('CampaignStationsAuthored2_20260930','CampaignStationsAuthored3_20260930','CampaignStationsAuthored4_20260930','CampaignStationsAuthored5_20261001'):
  for row in json.loads((ROOT/'Saved/CampaignAcceptance'/nm/'index.json').read_text())['placed']:
   stands+=[(a['label'],a['stand']) for a in row['actors']]
 stands+=[(h['label'],h['approach']) for h in json.loads((ROOT/'Saved/CampaignAcceptance/HospitalStationsAuthoredDeskTop_20260930/index.json').read_text())['stations']]
 S=SPEC['step'];cx,cy=SPEC['center'];H=SPEC['half'];zlo,zhi=SPEC['z']
 # 1) all standing-clear walkable layers per column
 layers={};floor_actor={}
 for ix in range(-int(H/S),int(H/S)+1):
  for iy in range(-int(H/S),int(H/S)+1):
   x,y=cx+ix*S,cy+iy*S;top=zhi;col=[]
   for _ in range(10):
    h=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,top),V(x,y,zlo),TQ,False,ignore,N,True))
    if not h:break
    z=h[5].z
    if h[7].z>=.707:
     # Standing clearance above a 32 cm step zone (risers below that are stepped over), up to 1.92 m.
     c=V(x,y,z+112)
     if not t(unreal.SystemLibrary.capsule_trace_single(world,c,c+V(0,0,.1),42,80,TQ,False,ignore,N,True)):
      col.append(round(z,1));floor_actor[(ix,iy,round(z,1))]=label(h)
    top=z-40
   if col:layers[(ix,iy)]=col
 nodes=[(ix,iy,z) for (ix,iy),zs in layers.items() for z in zs]
 R['walkable_cells']=len(nodes);R['map_seconds']=round(time.time()-t0)
 def wpos(n):return V(cx+n[0]*S,cy+n[1]*S,n[2])
 def edge(a,b):
  pa,pb=wpos(a),wpos(b);dz=b[2]-a[2]
  if dz>STEP_UP or dz<-MAX_DROP:return False
  if dz>=-STEP_UP:
   hi,lo=max(a[2],b[2]),min(a[2],b[2])
   m=t(unreal.SystemLibrary.line_trace_single(world,V((pa.x+pb.x)/2,(pa.y+pb.y)/2,hi+60),V((pa.x+pb.x)/2,(pa.y+pb.y)/2,lo-80),TQ,False,ignore,N,True))
   if not m or m[5].z<lo-20 or m[5].z>hi+20:return False
   # Body between the step zone and chest height; head room is covered by each cell's standing test.
   z=hi+100
   return not t(unreal.SystemLibrary.capsule_trace_single(world,V(pa.x,pa.y,z),V(pb.x,pb.y,z),42,50,TQ,False,ignore,N,True))
  # drop: walk off at the upper level, then fall clear to the lower floor
  za=a[2]+98
  if t(unreal.SystemLibrary.capsule_trace_single(world,V(pa.x,pa.y,za),V(pb.x,pb.y,za),42,96,TQ,False,ignore,N,True)):return False
  return not t(unreal.SystemLibrary.capsule_trace_single(world,V(pb.x,pb.y,za),V(pb.x,pb.y,b[2]+98),42,96,TQ,False,ignore,N,True))
 # 2) entrance node
 inbox=lambda p:abs(p[0]-cx)<=H and abs(p[1]-cy)<=H and zlo<=p[2]-98<=zhi
 box_anchors=[p for p in anchors if inbox(p)]
 R['route_anchors_in_box']=len(box_anchors)
 if box_anchors:
  # Seed from the route-proven anchor nearest the nominal entrance.
  e=min(box_anchors,key=lambda p:math.dist(p,SPEC['entrance']));SPEC['entrance']=(e[0],e[1],e[2]-98)
 ex,ey,ez=SPEC['entrance'];eix,eiy=round((ex-cx)/S),round((ey-cy)/S)
 cands=[(eix+dx,eiy+dy,z) for dx in range(-4,5) for dy in range(-4,5) for z in layers.get((eix+dx,eiy+dy),[])]
 assert cands,'No walkable cell near the entrance'
 start=min(cands,key=lambda n:math.dist(wpos(n).to_tuple(),(ex,ey,ez)))
 R['entrance_cell']=list(wpos(start).to_tuple())
 # 3) forward reach with stored edges
 out=collections.defaultdict(list);seen={start};q=collections.deque([start])
 while q:
  a=q.popleft()
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   for z in layers.get((a[0]+dx,a[1]+dy),[]):
    b=(a[0]+dx,a[1]+dy,z)
    if edge(a,b):
     out[a].append(b)
     if b not in seen:seen.add(b);q.append(b)
 # 4) backward reach inside the forward set
 rev=collections.defaultdict(list)
 for a,bs in out.items():
  for b in bs:rev[b].append(a)
 back={start};q=collections.deque([start])
 while q:
  b=q.popleft()
  for a in rev[b]:
   if a not in back:back.add(a);q.append(a)
 traps=seen-back;unreach=set(nodes)-seen
 # Where players fall into traps (returnable cell -> trap cell), and where a trap cell borders returnable
 # floor at walking height but the move out is blocked (candidate exits to clear).
 R['trap_entries']=[[[round(v) for v in wpos(a).to_tuple()],[round(v) for v in wpos(b).to_tuple()]] for a in back for b in out[a] if b in traps][:600]
 blocked=[]
 for c in traps:
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   for z in layers.get((c[0]+dx,c[1]+dy),[]):
    n=(c[0]+dx,c[1]+dy,z)
    if n in back and abs(z-c[2])<=STEP_UP:blocked.append([[round(v) for v in wpos(c).to_tuple()],[round(v) for v in wpos(n).to_tuple()]])
 R['trap_blocked_exits']=blocked[:600]
 def clusters(cells):
  cells=set(cells);bycol=collections.defaultdict(list)
  for c in cells:bycol[(c[0],c[1])].append(c)
  res=[]
  while cells:
   s=cells.pop();comp=[s];q=collections.deque([s])
   while q:
    a=q.popleft()
    for dx in (-1,0,1):
     for dy in (-1,0,1):
      for b in bycol.get((a[0]+dx,a[1]+dy),()):
       if b in cells and abs(b[2]-a[2])<=60:cells.discard(b);comp.append(b);q.append(b)
   ps=[wpos(c) for c in comp];area=len(comp)*(S/100)**2
   res.append({'cells':len(comp),'area_m2':round(area,1),'centroid':[round(sum(p.x for p in ps)/len(ps)),round(sum(p.y for p in ps)/len(ps)),round(sum(p.z for p in ps)/len(ps))],
    'z_range':[round(min(p.z for p in ps)),round(max(p.z for p in ps))],'floors':collections.Counter(floor_actor.get(c,'') for c in comp).most_common(4)})
  return sorted(res,key=lambda r:-r['cells'])
 def cell_of(p):
  ix,iy=round((p[0]-cx)/S),round((p[1]-cy)/S);best=None
  for dx in (-1,0,1):
   for dy in (-1,0,1):
    for z in layers.get((ix+dx,iy+dy),[]):
     d=math.dist(wpos((ix+dx,iy+dy,z)).to_tuple(),(p[0],p[1],p[2]-98))
     if d<120 and (best is None or d<best[0]):best=(d,(ix+dx,iy+dy,z))
  return best[1] if best else None
 checks=[('anchor_%d'%i,p) for i,p in enumerate(box_anchors)]+[(l,p) for l,p in stands if inbox(p)]
 R['checkpoints']=[]
 for lab,p in checks:
  c=cell_of(p)
  R['checkpoints'].append({'label':lab,'point':p,'cell_found':bool(c),'reachable':c in seen if c else None,'returnable':c in back if c else None})
 R.update(reachable=len(seen),returnable=len(back),traps=clusters(traps),unreachable=[c for c in clusters(unreach) if c['area_m2']>=4],
  reachable_z_range=[round(min(n[2] for n in seen)),round(max(n[2] for n in seen))],seconds=round(time.time()-t0))
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
