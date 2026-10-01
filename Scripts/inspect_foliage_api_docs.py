import unreal
out=[]
for m in ('get_instance_transforms','remove_all_instances','add_instances','get_used_foliage_types'):
 out.append(m+': '+(getattr(unreal.InstancedFoliageActor,m).__doc__ or ''))
open(r'F:\Carnival\Saved\CampaignAcceptance\FoliageApiDocs.txt','w').write('\n\n'.join(out))
