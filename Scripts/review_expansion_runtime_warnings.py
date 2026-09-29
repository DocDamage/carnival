"""Summarize verified package diagnostics without treating launch as visual acceptance."""
import argparse
import json
import re
from pathlib import Path

root = Path(r'F:\Carnival')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--runtime', type=Path, default=Path(r'I:\Carnival_WorldExpansion_HorrorPaint_FreshRecook_FS\Windows\HorrorPaint_PostRecook_DX12_Startup.log'))
parser.add_argument('--cook', type=Path, default=Path(r'I:\Carnival_WorldExpansion_HorrorPaint_FreshRecook_20260929_UAT.log'))
parser.add_argument('--report', type=Path, default=root / 'Saved/WorldExpansion/Runtime_Warning_Review.json')
args = parser.parse_args()
runtime, cook = args.runtime, args.cook
text = runtime.read_text(encoding='utf-8', errors='replace')
cook_text = cook.read_text(encoding='utf-8', errors='replace')
patterns = {'metahuman_missing_template': 'Could not find template object',
            'invalid_shader_maps': 'invalid ShaderMap', 'missing_root_physics': 'Could not find root physics body',
            'fatal_error': 'Fatal error', 'bad_import_index': 'Bad import index',
            'unhandled_exception': 'Unhandled Exception',
            'dx12_descriptor_exhaustion': 'Descriptor cache ran out of sub allocated descriptor blocks',
            'dx12_heap_rollover': 'OnlineHeap RollOver Detected'}
report = {'runtime_log': str(runtime), 'cook_log': str(cook),
          'counts': {key: text.count(value) for key, value in patterns.items()},
          'collections': sorted(set(re.findall(r'/Game/Carnival/Crowd/Collections/[^\s()]+', text))),
          'root_body_warnings': [line for line in text.splitlines() if 'Could not find root physics body' in line],
          'sm5_x4510_count': sum('X4510' in line for line in cook_text.splitlines()),
          'sm5_x4510_lines': sorted(set(line.strip() for line in cook_text.splitlines() if 'X4510' in line)),
          'material_compile_failures': sorted(set(line.split('Warning:')[-1].strip() for line in cook_text.splitlines() if 'Failed to compile Material' in line)),
          'interpretation': {
              'metahuman': 'DefaultInstance template imports refer to an editor-only MetaHumanCollection default subobject. Runtime assembly/appearance remains unaccepted; no collection assets changed to suppress errors.',
              'materials': 'SM5 sampler-limit compiler failures and invalid cooked ShaderMaps require material/permutation repair and fresh rendered verification. DX12 startup alone does not verify crowd skins.',
              'shipwreck': 'Source_Inspection.json identifies the source actor as SM_Sails_Torn. Engine SkeletalMeshComponentPhysics.cpp returns early from InitArticulated when FindRootBodyIndex fails. This prevents articulated-body initialization; rendering alone cannot prove sail/cloth physics works. Inspect the saved copied actor and PA_Sails_PhysicsAsset before choosing a repair.',
              'dx12_heap': 'When present, descriptor exhaustion switches to a context-local heap strategy. Startup survival does not establish performance; measure descriptor use and frame time before changing heap sizing.',
              'input': 'Source search found fixed mappings and saved sensitivity/dead-zone settings, but no player key-rebinding implementation. Remapping is an implementation gap, not a completed acceptance check.',
              'physical_controller': 'No physical DualSense input was performed.'}}
destination = args.report
destination.write_text(json.dumps(report, indent=2))
print(json.dumps({'report': str(destination), 'counts': report['counts'], 'x4510_count': report['sm5_x4510_count']}))
