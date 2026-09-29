# Gameplay systems implementation and acceptance

September 29, 2026 source changes. These are implementation changes; authored-world and physical-controller acceptance remain separate.

## Activities and targets

- Player overlap now supplies the nearby activity used by context interaction. Starting an active activity cannot erase its progress or replace another active activity.
- NPCs cannot collect player targets. Activity targets reject hits outside their active run or from another player. Target membership and per-run scoring prevent duplicate or unrelated callbacks from awarding points.
- Checkpoints require the active run and the next index. Completion cannot be overwritten by a late timeout callback; timers clamp to zero. Cancel/retry restore targets and clear the player's activity link.
- Collectible bobbing is relative to the saved position instead of accumulating movement every frame.

## Combat and building

- Equipped weapons perform visibility-blocked melee sweeps or revolver traces, apply point damage, enforce fire intervals, and expose last-hit/damage feedback. Configured impact Niagara effects are spawned on contact.
- Unarmed attacks now apply swept point damage with a per-player cooldown. Punch/kick alternation is per character.
- Building requires a surface, checks ground after grid snapping, aligns the mesh bottom above that surface, and rejects blocked placements including the player's capsule. Placement refreshes the preview before committing. Demolition remains restricted to the player's placed pieces.

## Boat and hovercraft lifecycle

- Mounting requires a nearby, stationary vehicle, a controller, and a rider who is not already seated elsewhere. The approach is capsule-swept so a nearby vehicle cannot be boarded through a wall. Carnival's enhanced input controller avoids duplicate legacy pawn bindings.
- Dismounts require low speed and a supported, capsule-clear exit with a clear path. No clear exit leaves the player aboard.
- Unpossessing clears held controls. Unexpected possession loss and vehicle destruction restore the rider, collision, movement, and available controller; emergency recovery can use the saved boarding position.
- Boat braking suppresses propulsion. Hovercraft fall when no ground supports them. Blocking sweeps clear vehicle velocity.
- **Open:** authored boat water detection/boundaries, shoreline boarding/dismounts, actual vehicle asset layout and animations, both-direction routes, and physical-controller acceptance.

## Parkour

- Vaults and mantles use capsule-validated raise/traverse/land paths. Movement is swept throughout and cancels if a new obstacle enters the path. Completion and cancellation restore walking or falling and stop the action montage.
- Traversal blocks movement, posture, building, combat, weapon switching and context/ride interactions until it completes or the player cancels. Root motion is consumed while native movement is disabled, and the montage stops without a movement-producing blendout on completion.
- Prone transitions preserve floor contact and refuse to stand when the full standing capsule would intersect a low ceiling.
- `ACarnivalLadder` exposes `BottomExit` and `TopExit` floor markers. Jump near either end attempts a checked ascent/descent. Cancel releases the player to normal movement. Both marker destinations must have walkable support.
- **Open:** placement/tuning of ladder markers on authored ladders, animation alignment, camera clearance and timing in real interiors. The new class alone does not make every existing decorative ladder usable.

## Verification

Automation coverage is in `Source/CarnivalGame/CarnivalGameplaySystemsTests.cpp`:

- `Carnival.Activities.LifecycleAndScoring`
- `Carnival.Combat.HitDamageAndOcclusion`
- `Carnival.Building.SupportedPlacement`
- `Carnival.Vehicles.BoardingAndRecovery`
- `Carnival.Parkour.ClearanceTraversalAndLadder`
- `Carnival.Motorcycle.ChaosControlsAndModeTransition`
- `Carnival.Rides.BumperDrivingAndHandover`
- `Carnival.Rides.PassengerScalePreservation`

The last fully passing audio-enabled Carnival automation baseline passed **32/32 tests: 31 clean passes and one pass with warnings, zero failures or not-run tests**. The warning belongs to the Balloon ground-station fixture (vendor SetAutoActivate) and is being addressed separately. This includes unarmed hits, mounted activity scoring with the actual possessed vehicle, boat/hover camera input properties, mount-path obstruction, prone ceiling clearance, vault/mantle and ladder round trips, Chaos controls, bumper driving and handover, and passenger scale preservation. The physics fixtures advance Unreal's frame counter between simulated world ticks so the physics tick actually executes each step. These tests use temporary native fixtures; they do not substitute for authored-world or physical-controller acceptance.

## Bumper cars and passenger scale

- Dedicated bumper pawns support throttle/reverse, steering, brake priority, swept collision and rebound, supported-floor checks and measured arena boundaries. The existing attended ride operation has a distinct DrivingArena experience which gates propulsion, stops cars before unloading, and retains passengers if all safe exits are obstructed.
- Boarding sweeps the player capsule to the driver seat, transfers possession to the car and uses the existing ride-passenger animation lifecycle. Exit and operator stop start a controlled stop; safe unloading restores the original player and collision. Destruction recovers the rider and controller.
- Shared vehicle mappings, mounted remapping selection, settings input clearing and HUD prompts include bumper cars. Prompts show current bindings.
- Passenger boarding/tracking preserve the player's original world scale beneath scaled ride components. Bumper seats use absolute unit scale; authoring owns visual seat placement.
- Native automation passes, including blocked approach/unloading, boundary containment, driving/braking/steering, operator handback, destruction recovery and scaled-seat regression. Project-only authoring saved eleven native cars, an attendant and a queue marker successfully. The first placed-world PIE attempt was rejected at boarding; detailed production precondition and capsule-sweep diagnostics are now prepared. Actual-world driving/unloading and rendered seat fit remain unverified.

## MetaHuman material repair status

- Local copies of the crowd skin master, five affected material functions and two MIC parent variants replace twelve verified wrap/default-filter samplers with shared wrap samplers. Vendor assets remain unchanged.
- The saved repair reparents 68 generated material instances while retaining 64 character-specific embedded parent links. Six collections also save their existing build-pipeline actor/instanced parent overrides to the project-local parents.
- Pipeline subclass properties require native reflected property spelling when Python wraps the object as its base class. No engine modification or project native helper is needed.
- A fresh SM5 cook and rendered comparison are still required; old cooked packages are not valid evidence after these schema/material changes.
- Subsequent SM6 rendering exposed a repair regression: 39 missing groom-function inputs in the local copied graph. The failing log is preserved in `Saved/CharacterRepairs/SamplerRepair_MissingFunctionInputs_20260929.txt`. Recovery restores exact original expression connections, output indices and masks into local graphs using `CarnivalMaterialRepairLibrary`, refreshes local function pin IDs, and refuses saves on reported material compiler errors. `Scripts/repair_crowd_sampler_graph_connections.py` successfully restored all six graphs (921 expressions), compiled with an empty compiler-error list and saved all six local packages. Fresh-load rendering and SM5 cooking remain required; see `Saved/CharacterRepairs/CrowdSamplerGraphRecovery.json`.

## Chaos motorcycle changes verified in native automation

- Physics input now handles brake priority, handbrake, analog L2 braking/reverse, grounded traction, airborne detection, lateral grip, steering and balance torque.
- Mode switching requires an authored skeletal physics body and preserves forward/vertical motion. A missing body retains arcade mode.
- Wheel animation and blocked-movement tracking measure completed Chaos movement between ticks, rather than the zero displacement immediately around deferred force calls.
- `Carnival.Motorcycle.ChaosControlsAndModeTransition` uses the saved physical body with gravity disabled to isolate input-force behavior. Suspension, tipping, stunt animation and the complete physical-mode experience still need rendered acceptance.

## Audio and prompt readability verification

- A game-instance audio settings subsystem saves master volume to the existing user settings file, clamps invalid gains, applies gain/mute to the active audio device and reapplies when the player controller begins play. The settings menu appends a master-volume row while preserving the remapping row.
- `Carnival.Audio.VolumePersistenceAndApplication` checks isolated on-disk persistence, reload, clamp, paused controller navigation and, when audio is enabled, reads gain/mute back from the actual audio thread. A `-nosound` run explicitly reports device application unavailable; it cannot establish that portion of acceptance.
- The OpenControlRemapping production API delegates the existing menu behavior and compiled successfully. Scripts/review_settings_readability_pie.py captures real settings and keyboard/gamepad remapping HUDs at 1280x800, 800x600 and 640x480. It changes no saved preferences and does not claim physical input.
- HUD boxes measure the real font, wrap long prompt/key-label text, grow at unchanged font size, preserve centered/bottom placement and stay inside the viewport. Extreme viewport overflow is truncated visibly. Multi-panel layout and legibility still need rendered checks.
- `Scripts/inspect_level_audio_census.py` records connected-world audio components, numerical gain values and attenuation data without changing assets. This is a diagnostic census, not an audition or proof of a balanced mix. Separate music/effects/dialogue routing is not claimed.

## Remaining authored acceptance

These changes do not establish finished authored activities, opponent health/AI/combat content, all building menus and persistence, every motorcycle stunt or Chaos mode, or all locations. The motorcycle ramp launch fix already existed with `Carnival.Motorcycle.RampLaunch`; the older checklist statement that launch velocity is immediately discarded was stale.

Character/content blockers remain distinct: the saved runtime warning review records six MetaHuman collection template import errors, 70 invalid ShaderMaps, and a Shipwreck sail root-body physics warning. Crowd appearance, clothing, the required roster, navigation under full population, and fully active-scene performance still require asset repair and rendered measurement.
