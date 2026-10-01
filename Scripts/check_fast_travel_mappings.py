"""Read-only: travel mappings left in the two player input mapping contexts (fresh session check for B14)."""
import json,unreal
out={}
for c in ("/Game/Carnival/Input/IMC_CarnivalPlayer","/Game/Carnival/Input/IMC_CarnivalMotorcycle"):
    ctx=unreal.load_asset(c)
    ms=list(ctx.get_editor_property("default_key_mappings").get_editor_property("mappings"))
    out[c]={"count":len(ms),"travel":[m.get_editor_property("action").get_name() for m in ms if m.get_editor_property("action") and "Travel" in m.get_editor_property("action").get_name()]}
    try: out[c]["legacy_mappings"]=len(list(ctx.get_editor_property("mappings")))
    except Exception as e: out[c]["legacy_mappings"]=str(e)[:80]
open(r"F:\Carnival\Saved\InputCleanup\travel_mapping_check.json","w").write(json.dumps(out,indent=1))
