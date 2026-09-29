"""Print compact current traversal evidence without launching Unreal."""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
report = json.loads(path.read_text(encoding="utf-8"))
print(json.dumps({
    "report": str(path), "success": report.get("success"),
    "tests": [{key: test.get(key) for key in ("name", "success", "seconds")}
              for test in report.get("tests", [])],
    "errors": report.get("errors", []),
    "phase": report.get("phase"),
}, indent=2))
