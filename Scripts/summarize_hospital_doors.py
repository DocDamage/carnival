"""Compact saved entrance audit evidence, including report modification time."""
import json
from pathlib import Path
path = Path(r"F:\Carnival\Saved\IndustrialHospital\Hospital_Door_Audit.json")
report = json.loads(path.read_text())
print(json.dumps({"mtime":path.stat().st_mtime,"errors":report["errors"],
    "entrance":report["entrance_sweeps"]}, indent=2))
