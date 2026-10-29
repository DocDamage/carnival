"""Repository checks that run without Unreal or locally licensed content.

Compile Python without importing/executing authoring scripts, validate JSON
descriptors, and reject whitespace errors or newly tracked ignored files.
This does not replace Unreal builds, native automation, or gameplay acceptance.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import warnings


ROOT = Path(__file__).resolve().parents[2]


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="", help="Commit to compare with HEAD")
    args = parser.parse_args()
    paths = [p.decode("utf-8") for p in git("ls-files", "-z").split(b"\0") if p]
    failures = []
    counts = {"python": 0, "json": 0}
    with warnings.catch_warnings():
        warnings.simplefilter("error", SyntaxWarning)
        for name in paths:
            path = ROOT / name
            try:
                if path.suffix == ".py":
                    compile(path.read_bytes(), name, "exec")
                    counts["python"] += 1
                elif path.suffix in (".json", ".uproject", ".uplugin"):
                    json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_keys)
                    counts["json"] += 1
            except (OSError, ValueError, SyntaxError, SyntaxWarning) as error:
                failures.append(f"{name}: {error}")
    if args.base and set(args.base) != {"0"}:
        # Resolve to a commit before passing the comparison to any other command.
        base = git("rev-parse", "--verify", args.base + "^{commit}").decode().strip()
        whitespace = subprocess.run(
            ["git", "-c", "core.safecrlf=false", "diff", "--check", base],
            cwd=ROOT, text=True, capture_output=True,
        )
        if whitespace.returncode:
            failures.append(whitespace.stdout + whitespace.stderr)
        changed = git("diff", "--name-only", "--diff-filter=ACMR", "-z", base)
        if changed:
            ignored = subprocess.run(
                ["git", "check-ignore", "--no-index", "-z", "--stdin"],
                cwd=ROOT, input=changed, capture_output=True,
            )
            if ignored.returncode not in (0, 1):
                failures.append(ignored.stderr.decode("utf-8", errors="replace"))
            if ignored.stdout:
                failures.append("Changed files must remain local/ignored: " + ", ".join(
                    p.decode("utf-8") for p in ignored.stdout.split(b"\0") if p))
    for failure in failures:
        print(failure, file=sys.stderr)
    print(f"Checked {counts['python']} Python files and {counts['json']} JSON descriptors.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
