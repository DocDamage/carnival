"""Trace supplied Amanda dependencies from measured full-scene load errors."""
import hashlib
import json
import re
import traceback
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/CharacterRepairs'
LOG = ROOT / 'Saved/PresentationAcceptance/PopulatedCarnival_AssetWaitColdCompileTimeout_20260930/index_engine.log'
PREFIX = '/Game/Fab/MetaHuman/'
SOURCE = '/Game/Carnival/MetaHumans/Additional/Amanda/AmandaBlack/'
REPORT = {'success': False, 'packages': [], 'missing_sources': [], 'errors': [],
          'limits': 'Read-only graph closure of dependencies actually missing in the preserved populated log.'}
try:
    blob = LOG.read_bytes()
    REPORT['source_log'] = str(LOG)
    REPORT['source_log_sha256'] = hashlib.sha256(blob).hexdigest()
    edges = sorted(set(re.findall(r'While trying to load package (\S+), a dependent package (\S+) \(', blob.decode(errors='replace'))))
    assert edges
    REPORT['observed_edges'] = [{'referencer': a, 'missing': b} for a, b in edges]
    queue = sorted({b for a, b in edges})
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,
        include_soft_package_references=True, include_searchable_names=False,
        include_hard_management_references=False, include_soft_management_references=False)
    seen = set()
    while queue:
        package = queue.pop(0)
        if package in seen:
            continue
        seen.add(package)
        assert package.startswith(PREFIX), package
        source_package = SOURCE + package.removeprefix('/Game/')
        source = ROOT / 'Content' / (source_package.removeprefix('/Game/') + '.uasset')
        if not source.exists():
            REPORT['missing_sources'].append({'package': package, 'source': str(source)})
            continue
        dependencies = sorted(str(p) for p in registry.get_dependencies(source_package, options))
        queue.extend(p for p in dependencies if p.startswith(PREFIX) and p not in seen)
        REPORT['packages'].append({'package': package, 'source_package': source_package,
            'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'dependencies': dependencies})
    assert REPORT['packages'] and not REPORT['missing_sources'], REPORT['missing_sources']
    REPORT['success'] = True
except Exception:
    REPORT['errors'].append(traceback.format_exc())
(OUT / 'AmandaLiveDependencyClosurePlan_20260930.json').write_text(json.dumps(REPORT, indent=2))
