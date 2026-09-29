"""Read-only export of existing ride seat meshes for measured seat authoring.

No map or asset is saved. OBJ geometry and component transforms are evidence,
not a claim that a passenger fits or that an attraction has passed acceptance.
"""
import json
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir()) / 'RideDevelopment' / 'SeatGeometry'
OUT.mkdir(parents=True, exist_ok=True)
inspection = json.loads((OUT.parent / 'Ride_Runtime_Inspection.json').read_text())
TOKENS = ('swing_chair', 'balloonride_seat', 'clownrideseat', 'sm_vehicle_01a',
          'mainboat_pirateride', 'teapot_ride_cup', 'sm_cabin_',
          'carousalbench', 'carousalhorse', 'hotair_balloon', 'bumpercar')
meshes = {}
for ride in inspection['rides']:
    for component in ride['components']:
        path = component.get('mesh', '')
        if path and any(token in path.lower() for token in TOKENS):
            meshes.setdefault(path, []).append({'ride': ride['path'], **component})

report = {'meshes': [], 'errors': [], 'source_assets_modified': False}
for path, components in meshes.items():
    try:
        mesh = unreal.load_asset(path)
        assert mesh, path
        destination = OUT / (mesh.get_name() + '.obj')
        task = unreal.AssetExportTask()
        task.object = mesh
        task.filename = str(destination)
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        task.exporter = unreal.StaticMeshExporterOBJ()
        assert unreal.Exporter.run_asset_export_task(task), path
        box = mesh.get_bounding_box()
        report['meshes'].append({'mesh': path, 'obj': str(destination),
            'unreal_bounds_min': list(box.min.to_tuple()), 'unreal_bounds_max': list(box.max.to_tuple()),
            'components': components})
    except Exception as exc:
        report['errors'].append({'mesh': path, 'error': repr(exc)})
        unreal.log_warning('RIDE_GEOMETRY ' + repr(exc))
(OUT / 'index.json').write_text(json.dumps(report, indent=2))
unreal.log('RIDE_GEOMETRY_EXPORT ' + json.dumps({'meshes': len(report['meshes']), 'errors': report['errors']}))
unreal.SystemLibrary.quit_editor()
