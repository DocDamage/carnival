"""Read-only connected-world audio settings and spatialization census.

Captures authored numerical values exactly; does not interpret vendor percent
controls as linear gain and does not claim audition/mix acceptance.
"""
import json
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/PresentationAcceptance/LevelAudioCensus.json'
REPORT={'modified_assets':False,'auditioned':False,'audio_components':[],'manager_properties':[],
        'sound_cue_graphs':{},'sound_classes':{},
        'findings':[],'errors':[]}


def prop(obj,name):
    try: return obj.get_editor_property(name)
    except Exception: return None


def settings(obj):
    if not obj: return None
    return {name:str(prop(obj,name)) for name in ('attenuate','spatialize','attenuation_shape','attenuation_shape_extents',
            'falloff_distance','attenuation_function','enable_occlusion','occlusion_trace_channel')}


def record_class(sound_class):
    if not sound_class: return None
    path=sound_class.get_path_name()
    if path in REPORT['sound_classes']: return path
    properties=prop(sound_class,'properties')
    REPORT['sound_classes'][path]={'parent':None,
        'properties':{name:prop(properties,name) for name in ('volume','pitch','is_music','is_ui_sound','apply_ambient_volumes')},
        'passive_mix_modifiers':str(prop(sound_class,'passive_sound_mix_modifiers'))}
    REPORT['sound_classes'][path]['parent']=record_class(prop(sound_class,'parent_class'))
    return path


def record_cue(sound):
    if not sound or not isinstance(sound,unreal.SoundCue): return None
    path=sound.get_path_name()
    if path in REPORT['sound_cue_graphs']: return path
    rows=[]
    REPORT['sound_cue_graphs'][path]=rows
    visited=set()
    pending=[prop(sound,'first_node')]
    while pending:
        node=pending.pop()
        if not node or node.get_path_name() in visited: continue
        visited.add(node.get_path_name())
        children=list(prop(node,'child_nodes') or [])
        attenuation=prop(node,'attenuation_settings')
        override=prop(node,'override_attenuation')
        effective=prop(node,'attenuation_overrides') if override else prop(attenuation,'attenuation')
        row={'node':node.get_path_name(),'class':node.get_class().get_name(),
             'children':[child.get_path_name() if child else None for child in children]}
        if effective: row['attenuation']=settings(effective)
        for name in ('input_volume','volume_min','volume_max','looping'):
            value=prop(node,name)
            if value is not None: row[name]=list(value) if name=='input_volume' else value
        sound_class=prop(node,'sound_class_override')
        if sound_class: row['sound_class_override']=record_class(sound_class)
        wave=prop(node,'sound_wave')
        if wave:
            row['wave']=str(wave)
            if hasattr(wave,'get_path_name'):
                row['wave_sound_class']=record_class(prop(wave,'sound_class_object'))
        rows.append(row)
        pending.extend(children)
    return path


try:
    world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        name=actor.get_class().get_name()
        if 'manager' in name.lower():
            REPORT['manager_properties'].append({'actor':actor.get_path_name(),
                'properties':list(unreal.CarnivalRideOperationComponent.describe_ride_properties(actor))})
        for component in actor.get_components_by_class(unreal.AudioComponent):
            sound=prop(component,'sound')
            attenuation=prop(component,'attenuation_settings')
            override=bool(prop(component,'override_attenuation'))
            sound_attenuation=prop(sound,'attenuation_settings') if sound else None
            sound_override=bool(prop(sound,'override_attenuation'))
            effective=(prop(component,'attenuation_overrides') if override else
                       prop(attenuation,'attenuation') if attenuation else
                       prop(sound,'attenuation_overrides') if sound_override else
                       prop(sound_attenuation,'attenuation'))
            cue=record_cue(sound)
            row={'actor':actor.get_path_name(),'component':component.get_name(),
                 'location':list(component.get_world_location().to_tuple()),
                 'sound':sound.get_path_name() if sound else None,
                 'sound_class':record_class(prop(sound,'sound_class_object')) if sound else None,
                 'sound_cue_graph':cue,
                 'component_volume_multiplier':prop(component,'volume_multiplier'),
                 'sound_volume_multiplier':prop(sound,'volume_multiplier') if sound else None,
                 'auto_activate':prop(component,'auto_activate'),
                 'allow_spatialization':prop(component,'allow_spatialization'),
                 'override_attenuation':override,'attenuation_asset':str(attenuation or sound_attenuation),
                 'effective_attenuation':settings(effective),'ui_sound':prop(component,'is_ui_sound'),
                 'sound_duration':prop(sound,'duration') if sound else None}
            REPORT['audio_components'].append(row)
            graph_attenuation=any('attenuation' in node for node in REPORT['sound_cue_graphs'].get(cue,[]))
            if sound and row['auto_activate'] and not effective and not graph_attenuation:
                REPORT['findings'].append({'component':component.get_path_name(),
                    'review':'Auto-active sound has no discovered component, sound or reachable SoundCue attenuation. Review intended global/spatial role and runtime overrides.'})
    REPORT['component_count']=len(REPORT['audio_components'])
except Exception:
    REPORT['errors'].append(traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(REPORT,indent=2,default=str))
    unreal.log('AUDIO_CENSUS '+json.dumps({'report':str(OUT),'components':len(REPORT['audio_components']),'errors':REPORT['errors']}))
    unreal.SystemLibrary.quit_editor()
