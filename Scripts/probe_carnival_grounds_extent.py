"""Read-only: spread of the Carnival persistent level props (2nd-98th percentile) and its PlayerStarts, to size the reachability audit box."""
import json,unreal
w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
xs=[];ys=[];zs=[];ps=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_level().get_outermost().get_name()!='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival':continue
    c=a.get_class().get_name()
    if c=='PlayerStart':ps.append(a.get_actor_location().to_tuple())
    if c not in('StaticMeshActor',) and not c.startswith('BP_'):continue
    o,e=a.get_actor_bounds(False)
    if e.x>3000 or e.y>3000:continue
    xs.append(o.x);ys.append(o.y);zs.append(o.z)
xs.sort();ys.sort();zs.sort();n=len(xs)
q=lambda v,f:round(v[int(f*(n-1))])
json.dump({'n':n,'x':[q(xs,0),q(xs,.02),q(xs,.5),q(xs,.98),q(xs,1)],'y':[q(ys,0),q(ys,.02),q(ys,.5),q(ys,.98),q(ys,1)],'z':[q(zs,0),q(zs,.02),q(zs,.5),q(zs,.98),q(zs,1)],'player_starts':ps},open(r'F:\Carnival\Saved\WorldExpansion\Reachability\carnival_extent_20261001.json','w'))
