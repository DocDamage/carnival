"""Restore only the registry-proven supplied crewneck dependency closure."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/CharacterRepairs'
live = len(sys.argv) > 1 and sys.argv[1] == '--live'
assert len(sys.argv) == (2 if live else 1), 'Only --live is supported'
stem = 'AmandaLiveDependencyClosure' if live else 'AmandaClothingDependencyClosure'
plan = json.loads((OUT / (stem + 'Plan_20260930.json')).read_text())
assert plan['success'] and not plan['missing_sources'] and not plan['errors']
report = {'success': False, 'copies': [], 'source_files_modified': False,
          'limits': 'Exact supplied dependency files; fresh material loading, compilation and appearance remain required.'}
pending = []
for row in plan['packages']:
    package = row['package']
    assert package.startswith('/Game/Fab/MetaHuman/' if live else '/Game/Fab/MetaHuman/OA_Crewneckt/')
    source = Path(row['source'])
    assert source.resolve().is_relative_to((ROOT / 'Content/Carnival/MetaHumans/Additional/Amanda/AmandaBlack').resolve())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == row['source_sha256']
    for extension in ('.uasset', '.uexp', '.ubulk'):
        origin = source.with_suffix(extension)
        if not origin.exists():
            continue
        destination = ROOT / 'Content' / (package.removeprefix('/Game/') + extension)
        digest = hashlib.sha256(origin.read_bytes()).hexdigest()
        if destination.exists():
            assert hashlib.sha256(destination.read_bytes()).hexdigest() == digest, str(destination)
        pending.append((package, origin, destination, digest))

for package, origin, destination, digest in pending:
    action = 'already_identical'
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, destination)
        action = 'copied'
    assert hashlib.sha256(origin.read_bytes()).hexdigest() == digest
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == digest
    report['copies'].append({'package': package, 'source': str(origin),
                            'destination': str(destination), 'sha256': digest, 'action': action})
report['success'] = True
(OUT / (stem + 'Copies_20260930.json')).write_text(json.dumps(report, indent=2))
print('Verified dependency closure:', len(pending), 'files;', sum(r['action'] == 'copied' for r in report['copies']), 'new copies')
