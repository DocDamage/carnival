"""Read-only site finder for the in-scope campaign stations beyond the hospital.

For each station: flood-fill walkable capsule nodes (1 m grid) from a known
region seed, then choose either existing fixtures or clear spots for spawned
props. A placement requires a reachable standing node, a station point outside
the fixture/prop bounds, a clear native-equivalent focus trace (stand+50 to
station+40) and, for three-control stations, each control being the nearest
station from its own standing node. Nothing is saved.
"""
import collections,hashlib,json,math,re,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CampaignAcceptance/StationSites20_20261001';OUT.mkdir(parents=True,exist_ok=False)
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
DESK='/Game/Town/Meshes/Props/SM_TableDesk.SM_TableDesk'
BOOKS='/Game/Hospital_Meshingun/Environment/Asset/Mesh/Props/SM_Book_Stack_01c.SM_Book_Stack_01c'
SWITCH='/Game/Docks/VOL2_Powell/Meshes/SM_SwitchBox.SM_SwitchBox'
# A plain pole: the mile-marker mesh prints '123', which confuses a 1-2-3 route.
MILE='/Game/Creepwood_Carnival_Meshingun/Environment/Asset/Mesh/Props/SM_Pole_01d.SM_Pole_01d'
CHEST='/Game/UnderwaterShip/Meshes/Props/CabinMetal/SM_LargeChest.SM_LargeChest'
PANEL='/Game/SciFiWorld/Meshes/SM_ControlPanel01.SM_ControlPanel01'
BOARD='/Game/Carnival/WorldExpansion/IndustrialSwitchboard/SM_IndustrialSwitchboard.SM_IndustrialSwitchboard'
W='L_CoastalMansionApproach'
FRONT_YAW={DESK:-90,CHEST:-90,BOARD:-90}
# kind: inspect (1) / controls (3 nearby) / route (3 spread). source: existing regex or spawned prop mesh.
SPECS=[
 dict(id='slums_workshop',level='L_IndustrialSlums_DistrictFinal',kind='inspect',prop=DESK,visual=BOOKS,seeds=[(46912,71854,73)],box=4500,prop_radius=4000,keep_clear_of='hospital_road'),
]
R={'success':False,'errors':[],'assets_saved':False,'stations':[],
 'limits':'Editor collision probes only. Spawned props are proposed, not placed. Does not establish PIE focus/dispatch, rendered readability, walked routes or performance.'}
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;NONE=unreal.DrawDebugTrace.NONE
WALK_IGNORE=[]
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
def name(h):return h[9].get_actor_label() if h and h[9] else ''
def floor_at(x,y,z_hi,z_lo):
 h=t(unreal.SystemLibrary.line_trace_single(world,V(x,y,z_hi),V(x,y,z_lo),TQ,False,WALK_IGNORE,NONE,True))
 return h[5] if h and h[7].z>=.707 else None
def capsule_hit(a,b):
 h=t(unreal.SystemLibrary.capsule_trace_single(world,a,b,42,96,TQ,False,WALK_IGNORE,NONE,True))
 # A walkable floor contact well below both centres is support, not an obstruction.
 if h and not (h[7].z>.707 and h[5].z<min(a.z,b.z)-60):return h
 return None
def find_seed(seed,step=100):
 sx,sy=round(seed[0]/step)*step,round(seed[1]/step)*step
 for r in range(0,11):
  ring=[(sx+dx*step,sy+dy*step) for dx in range(-r,r+1) for dy in range(-r,r+1) if max(abs(dx),abs(dy))==r]
  for k in ring:
   f=floor_at(*k,seed[2]+120,seed[2]-400)
   if not f:continue
   c=f+V(0,0,98)
   if not capsule_hit(c,c+V(1,0,0)):return k,c
 return None,None
FRONTIER=collections.Counter()
def edge_ok(a,b):
 """Step-aware walk test: continuous floor at the midpoint, body clear above a 50 cm step zone."""
 fa,fb=a.z-98,b.z-98;hi,lo=max(fa,fb),min(fa,fb)
 m=floor_at((a.x+b.x)/2,(a.y+b.y)/2,hi+60,lo-80)
 if not m or m.z<lo-20 or m.z>hi+20:FRONTIER['floor_gap']+=1;return False
 z=hi+50+60
 h=t(unreal.SystemLibrary.capsule_trace_single(world,V(a.x,a.y,z),V(b.x,b.y,z),42,60,TQ,False,WALK_IGNORE,NONE,True))
 if h:FRONTIER['body:'+name(h)]+=1
 return not h
def flood(seed,box,step=100):
 FRONTIER.clear();start,c=find_seed(seed,step)
 if not start:return {},None
 nodes={start:c};q=collections.deque([start])
 while q and len(nodes)<40000:
  k=q.popleft();p=nodes[k]
  for dx,dy in ((step,0),(-step,0),(0,step),(0,-step),(step,step),(step,-step),(-step,step),(-step,-step)):
   n=(k[0]+dx,k[1]+dy)
   if n in nodes or abs(n[0]-start[0])>box or abs(n[1]-start[1])>box:continue
   g=floor_at(*n,p.z-98+90,p.z-98-150)
   if not g:FRONTIER['no_floor']+=1;continue
   if abs(g.z-(p.z-98))>(105 if dx and dy else 75)*step/100:FRONTIER['rise_or_drop']+=1;continue
   c2=g+V(0,0,98)
   h=capsule_hit(c2,c2+V(1,0,0))
   if h:FRONTIER['standing:'+name(h)]+=1;continue
   if not edge_ok(p,c2):continue
   nodes[n]=c2;q.append(n)
 return nodes,start
def focus_clear(stand,point):
 return not t(unreal.SystemLibrary.line_trace_single(world,stand+V(0,0,50),point+V(0,0,40),TQ,False,[],NONE,True))
def face_point(o,e,stand,floor_z):
 """Closest AABB point to the stand, 12 cm outside, at reading height."""
 x=min(max(stand.x,o.x-e.x),o.x+e.x);y=min(max(stand.y,o.y-e.y),o.y+e.y)
 d=V(stand.x-x,stand.y-y,0);l=max(d.length(),1e-3)
 z=max(floor_z+40,min(o.z+e.z+5,floor_z+110))
 return V(x+d.x/l*12,y+d.y/l*12,z)
def sees_fixture(stand,actor,o):
 """Eye-level sight must reach the fixture itself, not a wall in front of or behind it."""
 h=t(unreal.SystemLibrary.line_trace_single(world,stand+V(0,0,50),o,TQ,False,[],NONE,True))
 return not h or h[9]==actor or (h[5]-o).length()<30
def best_stand(nodes,o,e,why,actor=None):
 best=None
 for k,c in nodes.items():
  if abs(k[0]-o.x)>e.x+300 or abs(k[1]-o.y)>e.y+300:continue
  ox=max(abs(c.x-o.x)-e.x,0);oy=max(abs(c.y-o.y)-e.y,0)
  gap=math.hypot(ox,oy)
  if gap<30 or gap>200:why['gap']+=1;continue
  p=face_point(o,e,c,c.z-98)
  if (p-c).length()>230:why['too_far_vertical']+=1;continue
  if not focus_clear(c,p):why['focus_blocked']+=1;continue
  if actor and not sees_fixture(c,actor,o):why['fixture_not_visible']+=1;continue
  if not best or gap<best[0]:best=(gap,k,c,p)
 return best
def mesh_extent(path,scale):
 m=unreal.load_asset(path);b=m.get_bounds()
 return V(b.box_extent.x*scale,b.box_extent.y*scale,b.box_extent.z*scale),b.origin*scale
def route_points(name):
 if name!='hospital_road':return None
 import sys;sys.path.insert(0,str(ROOT/'Scripts'))
 from industrial_hospital_route_config import world_point
 lay=json.loads((ROOT/'Saved/IndustrialHospital/Industrial_Hospital_Route_Meshes.json').read_text())
 return [tuple(world_point(p)[:2]) for p in lay['route_points_local_cm']]
ROUTE_FLOOR_WORDS=('road','route','segment','approach','walk','crossing','driveway','forecourt','trail')
def on_route_floor(px,py,e,z):
 for fx,fy in ((0,0),(1,1),(1,-1),(-1,1),(-1,-1)):
  q=(px+fx*(e+60),py+fy*(e+60))
  h=t(unreal.SystemLibrary.line_trace_single(world,V(q[0],q[1],z+150),V(q[0],q[1],z-300),TQ,False,[],NONE,True))
  if h and h[9] and any(w in h[9].get_actor_label().lower() for w in ROUTE_FLOOR_WORDS):return True
 return False
def prop_site(nodes,start,path,scale,taken,avoid=(),radius=1500,keep_clear=None):
 """Prop on a free floor spot beside a reachable stand node, facing it."""
 e,_=mesh_extent(path,scale);half=max(e.x,e.y)
 order=sorted((k for k in nodes if math.dist(k,start)<radius),key=lambda k:math.dist(k,start))
 for k in order:
  c=nodes[k]
  if any((c-a).length()<250 for a in avoid):continue
  for dx,dy in ((1,0),(0,1),(-1,0),(0,-1)):
   off=half+80;px,py=c.x+dx*off,c.y+dy*off
   g=floor_at(px,py,c.z+50,c.z-200)
   if not g or abs(g.z-(c.z-98))>25:continue
   if any(math.dist((px,py),tk)<half*2+60 for tk in taken):continue
   if keep_clear is None and on_route_floor(px,py,half,g.z):continue
   # Where the street itself is the road mesh (slums), keep props clear of the driving line instead.
   if keep_clear is not None and min(math.dist((px,py),q) for q in keep_clear)<600+half:continue
   # Meshes whose broad face is on Y need -90 so that face, not an edge, meets the stand.
   yaw=math.degrees(math.atan2(-dy,-dx))+FRONT_YAW.get(path,0)
   big=V(max(e.x,e.y)+5,max(e.x,e.y)+5,e.z)
   if t(unreal.SystemLibrary.box_trace_single(world,V(px,py,g.z+e.z+6),V(px,py,g.z+e.z+6.1),big,unreal.Rotator(0,0,0),TQ,False,[],NONE,True)):continue
   o=V(px,py,g.z+e.z);p=face_point(o,big,c,c.z-98)
   if not focus_clear(c,p):continue
   return {'prop_location':[px,py,g.z],'prop_yaw':yaw,'prop_extent':list(e.to_tuple()),'stand_node':k,'stand':c,'station':p}
 return None
def nearest_ok(rows):
 for r in rows:
  mine=(r['stand']-r['station']).length()
  if any((r['stand']-o['station']).length()<mine+40 for o in rows if o is not r):return False
 return True
try:
 before=hashlib.sha256(MAPFILE.read_bytes()).hexdigest()
 world=unreal.EditorLoadingAndSavingUtils.load_map(MAP);assert world
 allactors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 WALK_IGNORE.extend(a for a in allactors if a.get_actor_label().startswith('BP_MGate01'))
 R['walk_ignored']=[a.get_actor_label() for a in WALK_IGNORE]
 used_existing=set()
 for s in SPECS:
  row={'station':s['id'],'level':s['level'],'kind':s['kind'],'controls':[],'errors':[]}
  try:
   level=[a for a in allactors if '/'+s['level']+'.'+s['level']+':' in a.get_path_name()]
   count=1 if s['kind']=='inspect' else 3
   if s.get('targets'):
    # One flood from a connected seed; each marker sits at the reachable node nearest its target.
    nodes,start=flood(s['seeds'][0],s['box']);assert nodes,'No walkable seed'
    row['reachable_nodes']=len(nodes);taken=[];avoid=[]
    for i,target in enumerate(s['targets']):
     near=min(nodes,key=lambda k:math.dist(k,target));assert math.dist(near,target)<400,'Marker %d target not reachable'%(i+1)
     site=prop_site(nodes,near,s['prop'],s.get('prop_scale',1.),taken,avoid);assert site,'No marker site %d'%(i+1)
     taken.append(tuple(site['prop_location'][:2]));avoid.append(site['stand'])
     site.update(action=i+1,prop=s['prop'],prop_scale=s.get('prop_scale',1.),target_gap_cm=math.dist(near,target));row['controls'].append(site)
   elif s['kind']=='route' and 'prop' in s:
    taken=[]
    for i,seed in enumerate(s['seeds']):
     nodes,start=flood(seed,s['box']);assert nodes,'No walkable seed for marker %d'%(i+1)
     site=prop_site(nodes,start,s['prop'],s.get('prop_scale',1.),taken);assert site,'No marker site %d'%(i+1)
     taken.append(tuple(site['prop_location'][:2]));site.update(action=i+1,prop=s['prop'],prop_scale=s.get('prop_scale',1.),reachable_nodes=len(nodes));row['controls'].append(site)
   else:
    nodes,start=flood(s['seeds'][0],s['box'],s.get('step',100));assert nodes,'No walkable seed'
    row['frontier']=FRONTIER.most_common(12);row['reachable_nodes']=len(nodes);row['seed_node']=start;row['seed_z']=nodes[start].z-98
    if s.get('near')=='fixtures':
     fx=[a.get_actor_bounds(False)[0] for a in level if re.match(s['existing'],a.get_actor_label())]
     s['near']=(sum(v.x for v in fx)/len(fx),sum(v.y for v in fx)/len(fx))
    if 'near' in s:start=min(nodes,key=lambda k:math.dist(k,s['near']));row['near_node']=start;row['near_node_gap_cm']=math.dist(start,s['near']);assert row['near_node_gap_cm']<600,'Target area is not reachable from the region anchor'
    if 'existing' in s:
     cands=[];row['fixtures']=[]
     for a in level:
      if not re.match(s['existing'],a.get_actor_label()) or a.get_path_name() in used_existing:continue
      o,e=a.get_actor_bounds(False)
      why=collections.Counter()
      far=math.dist((o.x,o.y),start)>s['box']
      b=None if far else best_stand(nodes,o,e,why,a)
      row['fixtures'].append({'actor':a.get_actor_label(),'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()],'outside_box':far,'rejections':dict(why),'accepted':bool(b)})
      if b:cands.append({'actor':a.get_actor_label(),'path':a.get_path_name(),'stand_node':b[1],'stand':b[2],'station':b[3],'gap_cm':b[0]})
     row['candidate_count']=len(cands)
     spread=s.get('spread',200)
     if count==1:chosen=sorted(cands,key=lambda c:math.dist(c['stand_node'],start))[:1]
     else:
      chosen=None
      for a in sorted(cands,key=lambda c:math.dist(c['stand_node'],start)):
       group=[a]
       for b in sorted(cands,key=lambda c:(c['station']-a['station']).length()):
        if b in group or any((b['station']-g['station']).length()<spread or b['stand_node']==g['stand_node'] for g in group):continue
        if nearest_ok(group+[b]):group.append(b)
        if len(group)==3:break
       if len(group)==3:chosen=group;break
     assert chosen,'No fixture set satisfies spacing and nearest-focus'
     for i,c in enumerate(chosen):c['action']=0 if count==1 else i+1;used_existing.add(c['path']);row['controls'].append(c)
    else:
     taken=[];avoid=[]
     for i in range(count):
      site=prop_site(nodes,start,s['prop'],s.get('prop_scale',1.),taken,avoid,s.get('prop_radius',1500),route_points(s.get('keep_clear_of')))
      assert site,'No prop site %d'%(i+1)
      taken.append(tuple(site['prop_location'][:2]));avoid.append(site['stand'])
      site.update(action=0 if count==1 else i+1,prop=s['prop'],prop_scale=s.get('prop_scale',1.),visual=s.get('visual'))
      row['controls'].append(site)
     if count==3:assert nearest_ok(row['controls']),'Spawned controls fail nearest-focus'
  except Exception:row['errors'].append(traceback.format_exc())
  for c in row['controls']:
   for k in ('stand','station'):c[k]=list(c[k].to_tuple())
  R['stations'].append(row)
 assert hashlib.sha256(MAPFILE.read_bytes()).hexdigest()==before
 R['success']=all(not r['errors'] for r in R['stations'])
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
