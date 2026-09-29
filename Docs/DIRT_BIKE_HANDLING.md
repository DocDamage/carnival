# Dirt-bike handling target

The user specified GTA V dirt bikes as the motorcycle control reference on September 27, 2026. This is a handling and control-feel requirement, not a claim that the current vehicle matches that game. Blender is authorized for animation fixes.

## Required player behavior

- Responsive analog acceleration and steering, with useful low-speed control and stable high-speed response.
- Brake input must slow the bike even with throttle held. Release/cancel events must clear every driving input, including during dismount and possession changes.
- Controlled rear-wheel slides with recoverable grip, plus rider lean for wheelies, pitch adjustment over jumps, and stable landings.
- Clear separation between camera look and rider balance. Controller and keyboard inputs must both support the same maneuvers.
- Rider hands, feet, seat contact, body lean, and mount/dismount transitions must follow the bike convincingly. Correct animation or retargeting in Blender when needed.
- No route-specific automatic steering or speed restrictions in player gameplay. Automated route driving remains test code.

## Current implementation evidence

`CarnivalMotorcycle.cpp` provides an arcade mode and a separate Chaos mode. Brake priority is corrected and verified by `Carnival.Motorcycle.BrakePriority`: simultaneous throttle/brake stops forward and reverse travel, half brake produces proportional deceleration, and throttle resumes on release at 30/60/120 Hz. Ramp takeoff now preserves airborne state and upward velocity; `Carnival.Motorcycle.RampLaunch` passed at those rates. Ground alignment still uses one short downward ray and landing recovery remains unverified.

Acceleration now uses the exposed `Acceleration` rate instead of fixed interpolation. Driving API inputs are clamped, and losing possession clears throttle, steering, brake, and handbrake. The editor build passed; all three regressions passed, including `AccelerationAndRelease` at 30/60/120 Hz (3 passed, 0 failed/not-run). Existing full-route travel evidence predates this acceleration change and needs a repeat.

Arcade mode now exposes rear brake and rider balance. Rear-brake turns retain travel momentum while the bike yaws, then recover grip when released. Steering authority decreases at high speed. Pulling back under power raises the front; forward/back input adjusts airborne pitch independently of flight velocity. This is an initial arcade implementation, not final visual or hardware acceptance. Chaos mode still needs equivalent handling work.

`Carnival.Motorcycle.BalanceAndGrip` passes at 30/60/120 Hz: wheelie initiation/release without added altitude, rear-brake slip and grip recovery, opposite airborne pitch with matching flight trajectories, and recovery to a flat floor. All four motorcycle tests pass. The three ride tests also pass, including extended raw Enhanced Input dispatch checks for rear brake, balance, release, separate camera look, and keyboard mappings. These use simulated input, not a physical DualSense.

Saved bindings from `Scripts/setup_dirt_bike_input.py`: R1 / Left Alt rear brake; left stick back / Left Shift pulls back; left stick forward / Left Ctrl leans forward; right stick remains camera look. R2 throttle, L2 brake-to-reverse, Space brake, and W/S forward/reverse. L2 uses its own analog action: it reaches zero before backing up, opposing triggers hold a stop, and reverse propulsion requires ground support. Release, cancellation, dismount and possession loss clear the request. Original assets are backed up under `Saved/DirtBike/InputBackup_*`; `Input_Setup.json` records saved mappings.

F / Triangle calls the mounted stuck/overturn recovery routine before attempting a dismount. On foot, the same action rights the nearest overturned parked motorcycle without taking possession; a second press mounts it. The `MountRecovery` regression covers that full foot-to-recovery-to-mount loop alongside mounted stuck/overturn recovery, and passes in the 11-test motorcycle suite. Rendered PIE acceptance is still pending.

The full hospital route passed after the handling changes: 262.77 s outbound and 265.21 s return, no errors. Evidence is preserved in `Motorcycle_Route_PreBodyCollision.json`. Route driving uses conservative API-driven throttle and does not prove player handling quality.

The subsequent presentation audit found the saved bike had only its body mesh, no physics asset, and no driver-seat socket. The player mesh also had a sideways pitch rotation. The clips and displayed Manny use different skeleton asset paths, but that alone does not establish incompatibility; runtime playback is verified below.

`author_motorcycle_collision.py` now saves a backed-up body physics asset through `CarnivalVehicleAuthoring`. Imported root scale is 100 and roll is 90 degrees; the authoring conversion accounts for bone scale. Standard component sweeps misorient this root-bone geometry, so arcade movement now sweeps the component-space body bounds and clears speed on a wall impact. `Carnival.Motorcycle.SavedBodyCollision` drives the actual saved Blueprint against a solid wall at full speed: it advances from x=-1000 to x=-71.36 cm and stops with speed zero. All five motorcycle regressions pass. The raw editor `SetActorLocation` sweep in the presentation audit is not the arcade movement path and remains unsuitable for this imported bone transform.

The body-collision road round trip passed: 262.75 s outbound / 265.29 s return, no errors. This result predates the assembled vehicle below and is not a complete contact/obstacle test.

The supplied body, suspension and steering pieces are now assembled with separate rolling wheels, baked forward along +X in centimetres. The original FBX remains intact. Source riding-pose overlays showed the original bike was oversized; the authored model uses 75% scale, with 32.81 cm wheel radii and a 136.97 cm wheelbase. Derived files remain local under the ignored `Assembled` directory. `Assembly_Import.json` records imports and backups. The new root bone has identity rotation and scale 1, verified in automation.

The actual saved bike passes wheel installation, axle/ground alignment, distance-based rolling, steering, and stopped-wheel checks within `SavedBodyCollision`; all five motorcycle tests pass. A backed-up player Blueprint correction changes the mesh's erroneous -90 degree pitch to -90 degree yaw. Unreal renders confirm the complete bike and upright player (`Saved/DirtBike/Previews`). A real `DriverSeat` socket now reloads at (0,0,98.195) cm, accounting for the character mesh's -96 cm capsule offset and source floor correction.

`Carnival.Motorcycle.RiderPlayback` now spawns the saved rider and bike in a standalone runtime world, mounts at the actual seat socket, verifies all five mount/idle/dismount montages are accepted, and evaluates the riding pose through Manny's animation instance. Both feet lift into the seated pose (Z=28.113 cm; pelvis Z=109.299 cm). The rebuilt suite passes all six tests, with no warnings/failures/not-run. This establishes animation output, not correct physical contact or transition quality.

`Scripts/preview_motorcycle_rider.py` renders the saved riding clip frozen at 0.75 seconds on the saved Manny mesh and seat position. Three captures completed without errors; the side preview clearly shows hands below the grips and feet missing the pegs. These frozen inspection renders are separate from runtime montage verification. See `Saved/DirtBike/Previews/Rider_{Front,Rear,Side}.png` and `Rider_Capture_Report.json`.

The riding idle is now fitted in a local Manny-proportioned clip (`Fitted/Bike_Fitted_Idle`) with two-bone limb solving and matching foot-IK targets. The assembly includes authored foot rests centred at (0,±24,38) cm. Wrist targets are (34,±39,128) cm and ankle targets (-8,±25,46) cm; these are joint positions, not surface-contact points. Frozen Unreal renders show the lower natural leg pose with shoes on the rests and hands at the handlebars (`RiderFitted_Side.png`). Finger wrapping and moving contact still need review.

Runtime testing exposed Manny's post-slot foot correction lifting the entire fitted rider by 17.2 cm. A local copied graph `ABP_CarnivalManny` now blends the foot Control Rig with `1 - DisableLegIK`; the fitted clip supplies that curve at 1. The exposed AlphaCurveName pin must also be set or the compiler overwrites the struct setting with None. Normal animations without the curve retain full rig influence. The six-test suite passes the stricter runtime hand/foot target checks within 1 cm. `configure_mounted_animation_graph.py`, `fit_motorcycle_idle.py`, and `install_fitted_motorcycle_idle.py` reproduce the local assets and back up the player Blueprint. Original licensed assets remain unchanged.

Gameplay now loops the riding montage's first section instead of blending out and restarting each cycle. The rebuilt six-test suite passes the gameplay-start path, several idle cycles, and retained foot placement. Remaining: fit mount/dismount transitions and moving riding poses; correct wheelie rear-tyre ground contact and verify tyre clearance at obstacles (the current sweep is the body box); repeat road travel with the assembled mesh; validate high-speed uneven-ground handling, Chaos parity, and actual controller feel.

The newer eight-test suite adds saved-asset tyre contact and safe dismount coverage. Arcade motion now sweeps both tyres plus the authored chassis boxes. The chassis has a 32 cm lower half-width up to Z=80 cm and a full-width upper section; this avoids the old wide bounding box catching the floor during lean. At 30/60/120 Hz, the saved bike stops in forward/reverse with 0.25 cm tyre skin at a wall, sustains its full 2200 cm/s through a 30-degree lean, climbs a 30-degree slope, and raises the front tyre about 72 cm in a wheelie while keeping the rear supported. Release returns both tyres to the floor. These are controlled fixtures, not full off-road acceptance.

Ground sweeps follow the support plane. Downward tyre probes retain rear support across pavement edges, and low-curb stepping requires support plus clear upward/forward chassis sweeps. Tests cover 24 cm step-down/up and a low roof that prevents the climb. The first full-road run stopped at waypoint 59 because a centre-only support ray lowered the chassis while the rear wheel remained over raised carnival pavement. That failure and its collision-diagnostic probe are preserved in `Motorcycle_Route_TyreContact_Failure.json` and `Motorcycle_Tyre_Stall_Probe_Failure.json`. After tyre support was added, the focused stretch passed outbound in 25.03 s and return in 29.43 s. The subsequent full route must pass separately.

Dismount now checks floor support, capsule clearance, and the path from the seat; tries left/right and rear-side alternatives; and retains rider possession when all exits are blocked or unsupported. It places the disabled capsule outside the bike before restoring walking/collision, clears driving inputs, and selects the matching dismount montage. `SafeDismount` covers possession, both sides, a wall between seat and destination, and absent ground. Visual transition fitting and moving/airborne bailout behavior are not accepted by those checks.

Latest editor build: passed. Latest motorcycle tests: 8 passed, no warnings/failures/not-run; ride regressions: 3 passed, no warnings/failures/not-run. Full hospital-road rerun is in progress after the final chassis/curb changes. Remaining: finished mount/dismount and moving rider poses, complete uneven-ground/airborne collision and landing behavior, both connected-road retests, Chaos parity, physical controller feel, and all broader demo requirements.

## Acceptance evidence to collect

1. Measure acceleration, stopping distance with simultaneous throttle/brake, low-speed turning, high-speed steering, and input release at 30/60/120 Hz.
2. Test wheelie initiation/recovery, controlled slides, ramp launch, air pitch, landing recovery, slopes, steps, and collision with solid barriers. Repeat at practical riding speed on both connected routes.
3. Render and inspect rider contacts and mount/dismount from both sides, including uneven ground. Verify safe dismount clearance.
4. Run controller-only sessions with the user's DualSense and keyboard/mouse hot switching. Hardware feel remains unverified until an actual device test.
5. Repeat hospital turnaround and full outbound/return travel after handling changes. Preserve diagnostic failures; do not substitute a focused forecourt test for full-route acceptance.

The numeric tune should be chosen through these tests and player feedback. The GTA V reference does not justify claiming an exact match from API-driven traversal alone.
# Latest verification — 2026-09-27 airborne continuation

The assembled bike completed the full hospital round trip: 262.68 seconds outbound, 265.27 return, both successful with no reported errors. The formerly live session 87929 is terminal. This route used conservative automated throttle, before the subsequent airborne collision change.

Airborne vertical travel now sweeps chassis and tyre volumes, stops at ceilings, and lands on supported contact. Air attitude changes reject overlapping endpoints; the ground ray no longer snaps an airborne bike onto a distant floor. Native build and all nine motorcycle tests passed, including saved-bike fast falls onto a thin floor at three initial pitches, low ceilings, near-floor flight and wall-adjacent falls at 30/60/120 Hz. GTA V style controller feel and moving rider presentation remain unverified; these automated results do not complete that target.
