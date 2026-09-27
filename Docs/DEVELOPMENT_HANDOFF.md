# Carnival development handoff — updated 2026-09-27

This is the living project handoff. Resume from this document and the current working tree. **Do not restart the work or regenerate the entire project.** The original ride milestone below is retained; the latest milestone adds the opposite-side industrial slums and explorable hospital branch described near the end.

## Original ride milestone and verification (retained)

Implemented the first attended ride cycle, player boarding/unloading, operator handover, controller bindings, and an isolated playable swing test map. **The main carnival map does not yet have the new attendant placed.** Only the swing has an authored passenger seat layout. All rides remain in the agreed demo scope.

- Latest Unreal C++ editor build: **passed**.
- Latest automation run: **3 passed, 0 failed, 0 not run**, completed at 2026-09-27 04:27:36 UTC.
- Passing tests: `Carnival.Rides.AttendedSwing`, `Carnival.Rides.ControllerInput`, `Carnival.Rides.PassengerRecovery`.
- Swing test measured 1,354.88 cm maximum seat travel, 0.0000 cm passenger attachment error, three completed cycles, and walking restored after unloading.
- Tests load the actual vendor swing Blueprint and exercise its machinery, boarding, attachment, return, unloading, handover, and recovery. Input tests dispatch simulated raw gamepad keys through Enhanced Input, including release events.
- No physical DualSense hardware test or rendered/PIE inspection of the new map has been completed.
- `Scripts/preview_attended_swing.py` was just written and **has not been run**.
- No Unreal process or tool session remains running as of handoff.
- Changes are local and **uncommitted/unpushed**. Earlier user-requested GitHub push belonged to prior work and was already completed.

## User's agreed demo requirements

- Carnival, coastal wetlands/railroad bridge, and haunted mansion form one connected demo.
- Mansion approach takes roughly 3–5 minutes on foot; seamless motorcycle access as well.
- **Every carnival ride must be usable.** Player operator controls where they make sense; bumper cars need driving controls.
- **NPC attendants run every operating ride**: boarding, operating machinery, unloading, handing controls to players where appropriate, and resuming afterward.
- Carnival begins as a small lively midway, becoming ominous.
- Story combines a missing worker, music box, and strange lights/sounds. Worker is found alive and frightened in the mansion.
- Doll has stiff, twitchy possessed movement; first demo uses **scripted scares only, no failure/death/chase penalty**.
- After the mansion, return to carnival and keep using rides.
- Full modern controller support reminiscent of GTA V; **PS5 DualSense is the first test controller**.
- User authorizes substantive development and Blender animation work. Avoid unnecessary permission questions. No subagent delegation is currently authorized.

Planning documents from prior turns remain relevant, but have not yet been updated for this implementation milestone:

- `Docs/PLAYABLE_DEMO_CHECKLIST.md`
- `Docs/FIRST_DEMO_DESIGN.md`
- `Docs/CONTROLLER_AND_RIDE_CONTROLS.md`

## Environment and commands

Workspace `F:\Carnival`; PowerShell; Unreal 5.8.2 at `C:\Program Files\UE_5.8`.

Use the installed Python directly; earlier `cmd.exe` wrapper quoting failed. Run one Unreal process at a time to avoid memory contention. The wrapper launches without a visible helper window.

```powershell
# Build native code
& 'C:\Users\dferr\AppData\Local\Programs\Python\Python310\python.exe' 'F:\Carnival\Scripts\run_doll_tool.py' build

# Run the 3 ride/input tests
& 'C:\Users\dferr\AppData\Local\Programs\Python\Python310\python.exe' 'F:\Carnival\Scripts\run_doll_tool.py' ride-test

# Incremental input asset setup (already successfully run)
& 'C:\Users\dferr\AppData\Local\Programs\Python\Python310\python.exe' 'F:\Carnival\Scripts\run_doll_tool.py' unreal 'F:\Carnival\Scripts\setup_attended_rides.py'

# Attendant, seated animation, seat offsets, and test map (already successfully run)
& 'C:\Users\dferr\AppData\Local\Programs\Python\Python310\python.exe' 'F:\Carnival\Scripts\run_doll_tool.py' unreal 'F:\Carnival\Scripts\setup_swing_attendant.py'

# NEXT: rendered pose preview (script has not been exercised yet)
& 'C:\Users\dferr\AppData\Local\Programs\Python\Python310\python.exe' 'F:\Carnival\Scripts\run_doll_tool.py' editor 'F:\Carnival\Scripts\preview_attended_swing.py'
```

Wrapper modes also include `playtest` (full editor, null RHI, Python via ExecCmds), `unreal` (Python commandlet), and `test` (existing doll tests).

Read automation JSON, not just Unreal's exit code: Unreal may return zero even for failed tests. The wrapper now reads `index.json` and returns nonzero for failures/not-run/empty results.

## What changed in code

### Ride operation and attendants

New `Source/CarnivalGame/CarnivalRideOperationComponent.h/.cpp`:

- State machine: Closed → Loading → Securing → Running → Returning → Unloading → Loading.
- Default timing: boarding 5s, securing 2s, cycle 30s, return 6s, unloading 2s.
- One attendant owns operation; one player can temporarily take controls.
- Invokes vendor parameterless `StartRide` and `StopRide` via reflected UFunction, rather than merely changing the passenger phase enum.
- Captures movable child component home transforms; freezes actor tick, rotating movement and timelines during loading/return, then blends all children home before unloading.
- Disables the existing ride controller's automatic phase detection while managing it. Existing speed-only detection does not reliably handle purely rotating rides.
- Exit request while running initiates return; passengers remain seated until the ride reaches home.
- Restores each passenger to their own boarding transform, avoiding an unconfigured shared ride-origin exit.
- Losing the attendant safely returns/unloads and closes the ride.
- `DescribeRideControls` supports asset inspection. Verified all 11 inspected rides expose parameterless StartRide/StopRide/TurnOnRide/TurnOffRide.

New `Source/CarnivalGame/CarnivalRideAttendant.h/.cpp`:

- Character actor with Ride reference, display name, start/stop names, cycle duration, optional operator handover, idle/button animations.
- Creates or reuses the operation component on its assigned ride at BeginPlay; prevents two valid attendants claiming the same ride.
- Plays button animation during securing/returning and idle at other phases.
- Visual character is currently a **Manny mannequin prototype**, not a finished human employee.

### Passenger and player

Modified plugin passenger component under `Plugins/CarnivalMetaHumanKit/Source/CarnivalPopulation/`:

- Saves character movement mode, collision, facing settings and boarding transform.
- Disables movement/collision while attached; restores original settings on exit.
- Rejects duplicate boarding and seats belonging to another ride.
- Recovers after ride/seat destruction; passenger destruction releases occupied seat.

Modified `CarnivalPlayerCharacter`:

- Default `RidePassenger` component; nearby attendant selection; boarding/exit request; operator handover.
- Blocks normal movement/stance changes while riding or operating.
- Camera distance changes while seated.
- `RideSeatedAnimation` is a looping single-node animation; prior animation mode/class is restored on unloading.
- `OperatingRide` tracks current operation ownership.

### Controls and HUD

Modified `CarnivalPlayerController` and `CarnivalHUD`:

- Separate frame-rate-scaled stick look and mouse look; analog movement clamped to unit length.
- Contextual ride controls; seated jump blocked; attacks/build toggle blocked while using a ride.
- Tracks last input device and displays PlayStation button names by default; Xbox names available through `bPlayStationPrompts` setting.
- Ride prompt panel displays boarding, securing, running, returning and unloading status.
- Motorcycle throttle/steering/brake now handle Completed and Canceled events, preventing sticky inputs. Inputs also clear on unpossession.
- Sprint canceled event now clears sprint.

Current bindings in the saved assets:

| Action | DualSense layout | Keyboard |
|---|---|---|
| Move / camera | Left / right stick | WASD / mouse |
| Sprint / operator start | Cross | Shift |
| Jump / operator return | Square | Space |
| Board, request exit, mount/dismount | Triangle | F |
| Take operator controls | D-pad right | E |
| Hand controls back | Circle | Backspace |
| Crouch | L3 | C |
| Bike throttle / brake | R2 / L2 | W/S throttle-reverse, Space brake |

Options is mapped to the existing settings action, but complete pause/menu navigation is **not finished**. L2 is currently brake, not automatic reverse. No claim of full controller completion yet: hotplug, real DualSense transport, rumble, rebinding, menus, prompts across all activities, and accessibility settings remain.

## Authored assets and reports

Created:

- `/Game/Carnival/Rides/BP_RideAttendant`
- `/Game/Carnival/Rides/Maps/L_AttendedSwingTest` — isolated map with floor, daylight, swing, attendant, player start and carnival GameMode.
- `/Game/Carnival/Rides/Animations/Ride_AS_Sit_01` — retargeted to the existing player's Manny skeleton; locally licensed, now ignored by Git.
- `/Game/Carnival/Rides/Retarget/IK_RidePose_Source`, `IK_RidePose_Player`, `RTG_RidePose_Player`.
- Input actions `IA_LookStick`, `IA_RideOperate`, `IA_RideCancel`.

Updated:

- Both `IMC_CarnivalPlayer` and `IMC_CarnivalMotorcycle`.
- `BP_CarnivalPlayerController`, `BP_CarnivalPlayerCharacter`.
- `BP_Swing_Carnival`: 34 seat passenger offsets set to `(17, 0, 50)` cm. **This is a first calibration awaiting visual inspection.**

Evidence files:

- `Saved/HauntedDollIntegration/RideAutomation/index.json` — final passing automation report.
- `Saved/HauntedDollIntegration/Ride_Test.log` — individual assertions and metrics.
- `Saved/HauntedDollIntegration/build_console.log` — latest successful build.
- `Saved/RideDevelopment/Ride_Runtime_Inspection.json` — vendor APIs and component transforms for all inspected rides.
- `Saved/RideDevelopment/Controller_Setup.json` — authored bindings and source animation data.
- `Saved/RideDevelopment/Swing_Setup.json` — generated asset paths.
- `Saved/RideDevelopment/BeforeAttendedRides/` — original binary asset backups made before modifications.

## Important Unreal/Python findings

- `Key.import_text('F')` correctly mutates the key. Parenthesized `(KeyName=...)` is wrong for this importer.
- In UE 5.8, use `default_key_mappings.mappings`; the old `mappings` property is deprecated and may be empty.
- `map_key()` return-value edits did not persist the desired modifiers. The final setup script explicitly writes an `EnhancedActionKeyMapping` array back to `default_key_mappings` and forces asset save.
- Create input modifiers with **outer=context**, or modifiers can vanish on reload. This was fixed and verified by the final raw-input tests.
- `save_loaded_asset(asset, False)` forces saves for edits that otherwise fail to dirty the package.
- AnimSequence skeleton is read via `get_editor_property('skeleton')`, not `.skeleton`.
- Override `InputKey(const FInputKeyEventArgs&)` in UE 5.8; the older FInputKeyParams overload is final.
- A native test Character may start at MOVE_None. The attended-cycle test now explicitly starts walking physics; the separate recovery test checks restoration of MOVE_Flying and disabled collision.
- Python `unreal.Array += list` can yield None; convert to a regular list first.
- Existing duplicate Mansion/MansionNight external actor warnings predate this work. Avoid unrelated cleanup.
- Render with `r.RDG.ParallelExecute 0` to avoid the previously observed rendering residency crash.

## Prior ride-focused next development steps (resume after branch acceptance)

1. Run `preview_attended_swing.py` and inspect its two output images. Fix seated pelvis height/orientation, limb/chair intersections and staff appearance/position. The preview script is untested and may need Python API fixes. It renders an unsaved preview and should not overwrite the test map.
2. Run an actual PIE test of `L_AttendedSwingTest` using the real player Blueprint: approach attendant, board, watch a whole cycle, request early exit, operate, hand back, board again. Check character animation restoration, camera and HUD. Automation already passes; repeat it only if code/assets change.
3. Place the attendant beside the **existing main-map swing** at a clear, grounded approach point. Back up the licensed main map first. Add an appropriate control station; none has been made yet. Make placement idempotent with actor tags/labels and preserve other map actors.
4. Test the main-map interaction in PIE. The MetaHumanMassSpawner causes expensive unrelated outfit builds; previous route tests removed it only in the unsaved test world. Do not save that removal into the real map.
5. Review operation edge cases: vendor timers may restart motion after StopRide on other mechanisms; generic home-transform blending needs per-ride visual acceptance; exit positions currently reuse boarding positions without a fresh obstruction check; operator movement restoration currently forces walking. Complete cleanup/ownership review before broad rollout.
6. Extend to remaining rides, with appropriate authored seats and cycle behavior. Ferris/carousel loading positions need individual treatment; bumper cars need separate driving lifecycle. Do not advertise all rides as completed.
7. Replace prototype mannequin staff with suitable adult human characters and finish console gestures/handover. Existing MetaHuman presets are not all assembled runtime characters; avoid uncontrolled full crowd builds.
8. Update the three planning docs with verified progress and remaining work; then continue the mission/controller requirements. Do not publish licensed assets or claim a playable complete demo prematurely.

## Prior work already completed — retain it

- Main map `/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival`.
- Connected always-loaded levels `/Game/Carnival/World/Levels/L_CoastalMansionApproach` and `/Game/Carnival/World/Levels/L_HauntedMansionConnected`.
- Authored route about 1,028 m; previous API-driven traversal took 3:50 on foot at 450 cm/s and 2:41 by conservative motorcycle throttle. 570 floor samples had no blocking obstructions. No physical-controller validation yet.
- Remaining environment issues include strong glare/mansion lighting polish and performance profiling.
- Doll has a reusable 26-bone rig, 31 clips, native behavior and prior tests. **Its existing automatic chase behavior still needs to be gated off for this scripted-scare demo.** The mansion mission has not been built.
- Existing Carnival ride child Blueprints: Swing, PirateShip, BalloonTower, ClownRide, FlyingBobs, Circus, HauntedHouse, HotAirBalloon, Teapot. Only Swing has seats (34). Ferris/carousel are in lighting sublevels; bumper setup remains.
- **Do not rerun `Scripts/wire_ride.py` wholesale**: it deletes/recreates output Blueprints and can destroy the new seat calibration. `setup_complete_gameplay.py` also does broad unrelated mutations; use the new focused scripts.

## Working tree preservation

This session changed source, scripts, several project-owned Blueprints/input assets and `.gitignore`. Nothing has been committed. Inspect `git status` before continuing.

Verified branch: `main`. HEAD: `b3fa0cab` — `fix: stabilize connected world rendering and validate mansion travel`.

Preserve pre-existing untracked user content: `%SystemDrive%/`, `Content/Carnival/Crowd/`, `Content/Carnival/MetaHumans/`, `Content/Grooms/`, `Content/Outfits/`, `Content/PlayMusicAnim/`. These are not cleanup targets and should not be blindly staged.

Purchased source packs, the doll assets, connected licensed maps and retargeted licensed animations remain local. Existing `.gitignore` records exclusions; scripts and original code are the reproducible deliverable.

Prior ride-focused next-chat instruction (superseded while the hospital route awaits acceptance): **Read `F:\Carnival\Docs\DEVELOPMENT_HANDOFF.md`, inspect the current working tree, then resume at rendered/PIE validation of the attended swing and place its attendant in the main carnival. Preserve the requirement that every ride eventually has a working attendant and remains usable after the mansion sequence.**

## Opposite-Side Industrial Hospital Route — implemented; runtime acceptance pending

The Carnival now has a second branch from the opposite-side gate, crossing an industrial slum district and ending at the supplied abandoned hospital. The branch is attached to the persistent Carnival map as nine always-loaded sublevels, including the route, cropped slum district, hospital frontage, the hospital interior architecture/lights, and the source hospital's set dressing, decals, VFX, and volume levels. The user's supplied factory gate facade is placed at the hospital forecourt. The hospital interior remains intact and explorable in its source layout.

- Entry gate: `(7093.926, 6841.718, 42.781)` cm, yaw 54 degrees.
- Road length from Carnival exit to hospital door: about 1,536 m. At the route author's 450 cm/s walking reference, that is about 5:41. At a cautious motorcycle estimate of 6.4 m/s, about 4:00. These are layout estimates, not measured gameplay traversal times.
- Road has a 9 m clear lane and was built in seven chunks. The branch has exterior audio cues and six ambient audio sources, three along the route and three inside the hospital.
- The hospital assets' global atmosphere was omitted, and their authored directional light was excluded so the Carnival's night setting remains in use. The root map was saved with the new levels connected.
- Weather remains Carnival night snow. Five local fog cells grow progressively denser toward the hospital. The supplied legacy snow-flare effect was left out because it references a missing Village vector-field asset and created excessive bloom in preview.
- User-provided source packs and extracted licensed content stay local and ignored by Git. In particular, the audio source archive is `F:\Carnival\Assets\Abandoned Toy Factory.zip`; extracted Unreal audio is under `Content/Carnival/Audio/IndustrialHospital/`. The supplied exterior facade source is in `F:\Carnival\Assets\High facade of the factory with exit gates`. Do not redistribute these assets.

### Branch implementation and verification

Rebuild scripts are focused and can be run in this order when source assets are available: `prepare_industrial_hospital_sources.py`, `import_industrial_hospital_assets.py`, `sample_industrial_slums_terrain.py`, `build_industrial_slums_terrain_mesh.py`, `prepare_industrial_slums_district.py`, `finalize_industrial_slums_district.py`, `build_industrial_hospital_route_meshes.py`, `import_industrial_hospital_route_assets.py`, `prepare_hospital_interior_architecture.py`, `prepare_hospital_interior_lights.py`, `author_industrial_hospital_route.py`, `author_industrial_hospital_facade.py`, and `connect_industrial_hospital_world.py`. Use the project's `Scripts/run_doll_tool.py` Unreal mode for Unreal Python scripts. The connected capture is `capture_industrial_hospital_connected.py`.

Connection and authoring evidence is in `Saved/IndustrialHospital/World_Connection.json`, `Industrial_Hospital_Authoring.json`, and `Previews/Connected/Capture_Report.json`. The connection report records a backup of `LV_Carnival.umap` and the saved map hash. The connected capture opened the persistent map, found every expected new level, and returned no capture errors. Preview lighting selected Carnival's `Lv_LightingNightSnow` layer without saving that preview-only change to the root map.

### Remaining acceptance work

- The connected editor previews are still severely overexposed in the slum, hospital approach, and hospital interior views. Do not treat the preview as final visual acceptance; inspect and correct exposure/fog/lighting in the editor before calling the atmosphere finished. Preview images are in `Saved/IndustrialHospital/Previews/Connected/`.
- No PIE test has yet verified motorcycle traversal, road collision, slum/hospital transitions, or walking through the full hospital interior. Verify them in game, including the entrance alignment and interior doors.
- The root map was saved and all referenced sublevels loaded for capture, but that is not a substitute for runtime testing or packaged-build validation. The estimated travel times above have not been measured in gameplay.
- Preserve the existing Carnival night setup and the established mansion branch while tuning the hospital lighting/weather.

### Current branch-related file policy

- The persistent Carnival root map is the existing licensed project map at `/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival`.
- Authored branch maps are in `/Game/Carnival/World/Levels/`; this folder is already ignored because these copied demo layouts depend on local source assets.
- The cropped slum source content and hospital source pack under `Content/IndustrialSlums/` and `Content/Hospital_Meshingun/` are ignored. Extracted hospital ambience under `Content/Carnival/Audio/IndustrialHospital/` is now narrowly ignored too.
- Do not stage unrelated dirty ride, crowd, MetaHuman, or music-animation work when reviewing these branch changes. Nothing in this milestone was committed.

Suggested next work: **Read this handoff and `Docs/INDUSTRIAL_HOSPITAL_CONNECTION.md`, inspect the current working tree, then resolve the connected-preview exposure and verify motorcycle/foot traversal into and through the hospital in PIE. Preserve the existing mansion branch and continue the separate ride-attendant milestone afterward.**
