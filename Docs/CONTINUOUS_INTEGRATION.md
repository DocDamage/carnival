# Continuous integration

The `Source checks` GitHub Actions job runs on pull requests targeting `main`,
pushes to `main`, and manual dispatch. It checks every tracked Python script
without importing Unreal or executing authoring code, parses JSON project/plugin
descriptors with duplicate-key detection, and checks the proposed changes for
whitespace errors and files that Git explicitly ignores.

Run the same checks locally after staging new files:

```powershell
py -3 Scripts/ci/check_source.py --base origin/main
py -3 -m unittest discover -s Scripts/ci -p 'test_*.py'
```

`main` requires the `Source checks` status before merging. Repository auto-merge
allows a PR to merge after the required check succeeds and the branch is current.
The workflow has read-only repository permissions and uses pinned action commits.

Hosted CI does not build Unreal, run native/gameplay automation, or verify asset
appearance. The engine and licensed packs are absent from the public repository,
and no Unreal self-hosted runner is configured. Run the local engine checks:

```powershell
py -3 Scripts/run_doll_tool.py build
py -3 Scripts/run_doll_tool.py game-build
py -3 Scripts/run_doll_tool.py all-test
```

The October 29 water-vehicle checkpoint passes both builds and all 45 native
tests, plus connected-world headless recovery/braking/unloading and isolated
rendered HUD/camera checks. The handoff records the exact evidence and remaining
world-rendering, vehicle art/seating, hardware and complete-demo limitations.
Green hosted CI is source validation; it does not establish demo completion.
