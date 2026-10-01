import json,unreal
out={'classes':[n for n in dir(unreal) if 'oliage' in n]}
for n in out['classes']:
 c=getattr(unreal,n)
 out[n]=[m for m in dir(c) if not m.startswith('_') and ('instance' in m.lower() or 'remove' in m.lower() or 'foliage' in m.lower())]
open(r'F:\Carnival\Saved\CampaignAcceptance\FoliagePythonApi.json','w').write(json.dumps(out,indent=1))
