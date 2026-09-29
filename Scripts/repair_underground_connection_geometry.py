"""Cut real openings in copied expansion shells and correct stair enclosure slope.

Run with run_doll_tool.py unreal. Each source map is backed up before editing;
licensed meshes are never edited. Re-running leaves already repaired pieces intact.
"""
import datetime,json,math,shutil
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion'
LEVEL='/Game/Carnival/World/Levels/'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report={'success':False,'backups':[],'changes':[]}
prior=OUT/'Underground_Connection_Geometry_Repair.json'
if prior.exists(): shutil.copy2(prior,OUT/'Backups'/('Underground_Connection_Geometry_Repair_'+stamp+'.json'))

def open_map(name):
    package=LEVEL+name
    source=ROOT/('Content/Carnival/World/Levels/'+name+'.umap')
    backup=OUT/'Backups'/(name+'_before_underground_'+stamp+'.umap')
    shutil.copy2(source,backup); report['backups'].append(str(backup))
    world=unreal.EditorLoadingAndSavingUtils.load_map(package)
    if not world: raise RuntimeError('Cannot load '+package)
    return world,package

def save(world,package):
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,package): raise RuntimeError('Cannot save '+package)

def box(center,size,material,label):
    a=eas.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*center))
    a.set_actor_scale3d(unreal.Vector(*[x/100 for x in size])); a.set_actor_label(label)
    c=a.get_component_by_class(unreal.StaticMeshComponent)
    c.set_editor_property('static_mesh',unreal.load_asset('/Engine/BasicShapes/Cube'))
    if material: c.set_material(0,material)
    c.set_collision_profile_name('BlockAll')
    a.set_editor_property('tags',[unreal.Name('WorldExpansionConnectionRepair')])
    return a

def cut_box(actor_name,hole_min,hole_max,label):
    actors=list(eas.get_all_level_actors())
    if any(a.get_actor_label().startswith(label+'_Part') for a in actors): return
    a=next((a for a in actors if a.get_name()==actor_name or a.get_actor_label()==actor_name),None)
    if not a:
        if any(a.get_actor_label().startswith(label+'_Part') for a in actors): return
        raise RuntimeError('Missing expected boundary '+actor_name)
    center,extent=a.get_actor_bounds(False,True)
    c=a.get_component_by_class(unreal.StaticMeshComponent)
    if not c or c.get_editor_property('static_mesh').get_path_name()!='/Engine/BasicShapes/Cube.Cube': raise RuntimeError('Unexpected boundary mesh')
    lo=[center.to_tuple()[i]-extent.to_tuple()[i] for i in range(3)]
    hi=[center.to_tuple()[i]+extent.to_tuple()[i] for i in range(3)]
    h0=[max(lo[i],hole_min[i]) for i in range(3)]; h1=[min(hi[i],hole_max[i]) for i in range(3)]
    if any(h1[i]<=h0[i] for i in range(3)): raise RuntimeError('Cut misses '+label)
    material=c.get_material(0); remaining=[]
    # Six disjoint rectangular solids preserve everything outside the opening.
    for axis in range(3):
        for lower in (True,False):
            p,q=lo[:],hi[:]
            for prior in range(axis): p[prior],q[prior]=h0[prior],h1[prior]
            if lower: q[axis]=h0[axis]
            else: p[axis]=h1[axis]
            if all(q[i]-p[i]>.01 for i in range(3)): remaining.append((p,q))
    for i,(p,q) in enumerate(remaining): box([(p[k]+q[k])/2 for k in range(3)],[q[k]-p[k] for k in range(3)],material,label+'_Part'+str(i))
    report['changes'].append({'original':a.get_path_name(),'opening_local_min':h0,'opening_local_max':h1,'remaining_solids':len(remaining)})
    eas.destroy_actor(a)

try:
    world,package=open_map('L_CarnivalWorldExpansion_Sewers')
    # Sewer copy is streamed at (-27100,-12290,-1800).
    cut_box('StaticMeshActor_366',(640,2090,-40),(680,2890,540),'Sewer_Atlantis_Portal')
    cut_box('StaticMeshActor_367',(-250,-4710,1200),(450,-2210,1400),'Sewer_Stair_RoofOpening')
    arch_names={'StaticMeshActor_'+str(i) for i in (251,253,334,335,352,354,356,358)}
    for a in eas.get_all_level_actors():
        if a.get_name() in arch_names and 'StairClearanceMoved' not in [str(t) for t in a.get_editor_property('tags')]:
            old=a.get_actor_location(); a.set_actor_location(old+unreal.Vector(-450,0,0),False,True)
            a.set_editor_property('tags',list(a.get_editor_property('tags'))+[unreal.Name('StairClearanceMoved')])
            report['changes'].append({'actor':a.get_path_name(),'before':old.to_tuple(),'after':a.get_actor_location().to_tuple()})
    save(world,package)
    world,package=open_map('L_CarnivalWorldExpansion_Atlantis')
    # Atlantis copy is streamed at (-13000,-11000,-1800). Carve the descending portal.
    cut_box('StaticMeshActor_20',(5650,-300,-100),(7100,1750,100),'Atlantis_Shipwreck_Portal')
    cut_box('Atlantis_Ship_Exit_Pad',(5650,-300,-200),(7350,1750,100),'Atlantis_Shipwreck_ExitPadOpening')
    save(world,package)
    world,package=open_map('L_CarnivalWorldExpansion_Connections_Layout')
    corrected=0
    for a in eas.get_all_level_actors():
        if a.get_actor_label() in ('PrisonSewer_StairWall','PrisonSewer_StairCeiling'):
            a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=math.degrees(math.atan2(2400,6500))),True)
            s=a.get_actor_scale3d(); s.y=(math.hypot(6500,2400)/9+35)/100; a.set_actor_scale3d(s); corrected+=1
    if corrected!=27: raise RuntimeError('Unexpected enclosure count '+str(corrected))
    report['changes'].append({'stair_enclosure_corrected':corrected,'reason':'UE roll sign was opposite descent; use true sloped segment length'})
    save(world,package)
    report['success']=True
finally:
    (OUT/'Underground_Connection_Geometry_Repair.json').write_text(json.dumps(report,indent=2))
    unreal.SystemLibrary.quit_editor()
