"""Check skylight Python argument/return types on a transient unattached component."""
import json, traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
REPORT={'success':True,'assets_modified':False,'probes':{}}
component=unreal.SkyLightComponent()
for name, action in (
    ('color_argument', lambda: component.set_light_color(unreal.Color(255,255,255,255))),
    ('linear_color_argument', lambda: component.set_light_color(unreal.MathLibrary.conv_color_to_linear_color(unreal.Color(255,255,255,255)))),
    ('color_tuple', lambda: component.get_editor_property('light_color').to_tuple()),
    ('linear_color_tuple', lambda: component.get_editor_property('lower_hemisphere_color').to_tuple()),
    ('clear_cubemap', lambda: component.set_cubemap(None)),
    ('source_type', lambda: component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)),
    ('console_int', lambda: unreal.SystemLibrary.get_console_variable_int_value('r.DynamicGlobalIlluminationMethod'))):
    try:
        value=action(); REPORT['probes'][name]={'supported':True,'result':str(value)}
    except Exception:
        REPORT['probes'][name]={'supported':False,'error':traceback.format_exc()}
(ROOT/'Saved/PresentationAcceptance/NightFillApiProbe_20260930.json').write_text(json.dumps(REPORT,indent=2))
