"""Read lighting and post-process settings in the actual loaded world."""
import unreal


def properties(obj, names):
    result = {}
    for name in names:
        try:
            value = obj.get_editor_property(name)
            result[name] = value if isinstance(value, (str, int, float, bool)) or value is None else str(value)
        except Exception:
            result[name] = 'unavailable'
    return result


def survey(world):
    actors = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Light))
    actors += list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume))
    actors += [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
               if any(term in a.get_name().lower() for term in ('sky', 'daynight', 'weather'))]
    rows = []
    seen = set()
    fields = ('bloom_intensity', 'bloom_threshold', 'auto_exposure_method', 'auto_exposure_bias',
              'auto_exposure_min_brightness', 'auto_exposure_max_brightness',
              'auto_exposure_low_percent', 'auto_exposure_high_percent', 'indirect_lighting_intensity',
              'scene_color_tint', 'scene_fringe_intensity', 'color_saturation',
              'override_bloom_intensity', 'override_auto_exposure_bias', 'override_scene_fringe_intensity')
    for actor in actors:
        if actor.get_path_name() in seen:
            continue
        seen.add(actor.get_path_name())
        row = {'actor': actor.get_path_name(), 'label': actor.get_actor_label(),
               'class': actor.get_class().get_path_name(), 'location': list(actor.get_actor_location().to_tuple()),
               'lights': [], 'post_process': []}
        for light in actor.get_components_by_class(unreal.LightComponent):
            row['lights'].append({'component': light.get_path_name(), 'class': light.get_class().get_path_name(),
                                  'settings': properties(light, ('intensity', 'light_color', 'cast_shadows',
                                                               'indirect_lighting_intensity', 'volumetric_scattering_intensity',
                                                               'attenuation_radius', 'visible', 'affects_world',
                                                               'cubemap', 'source_type', 'lower_hemisphere_is_black'))})
        # SkyLight derives from LightComponentBase rather than LightComponent.
        for light in actor.get_components_by_class(unreal.SkyLightComponent):
            row['lights'].append({'component': light.get_path_name(), 'class': light.get_class().get_path_name(),
                                  'settings': properties(light, ('intensity', 'light_color', 'cast_shadows',
                                                               'indirect_lighting_intensity', 'visible', 'affects_world',
                                                               'cubemap', 'source_type', 'lower_hemisphere_is_black'))})
        if isinstance(actor, unreal.PostProcessVolume):
            row['volume'] = properties(actor, ('enabled', 'unbound', 'priority', 'blend_weight', 'blend_radius'))
            row['post_process'].append(properties(actor.get_editor_property('settings'), fields))
        for component in actor.get_components_by_class(unreal.PostProcessComponent):
            row['post_process'].append({'component': component.get_path_name(),
                                        'component_settings': properties(component, ('enabled', 'unbound', 'priority', 'blend_weight')),
                                        'settings': properties(component.get_editor_property('settings'), fields)})
        if row['lights'] or row['post_process']:
            rows.append(row)
    return {'actors': rows, 'assets_modified': False,
            'limits': 'Light actors, post-process volumes and sky/weather actor components. Camera blending and material/shader appearance need rendered comparison.'}
