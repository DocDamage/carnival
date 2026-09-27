# Playable demo checklist

Audit: September 27, 2026. Baseline implementation commit: `be6dff0b`.

The first-demo scope includes **the Carnival, coastal wetlands/railroad bridge, haunted mansion, industrial slums, and abandoned fully explorable hospital**, with seamless walking and motorcycle access. It also includes **every discussed project location and gameplay system**, every usable attendant-run Carnival ride, applicable player operator controls, a small lively midway that grows ominous, scripted doll scares without death or failure, full modern controller support, and the missing-worker/music-box story. DualSense is the first hardware test controller. On 2026-09-27, the user explicitly clarified that everything discussed is part of the first demo; earlier “deferred” labels below are superseded.

The core story combines a missing carnival worker, an old music box, and unexplained lights/sounds. The proposed connection is that the worker disappeared while recovering the box from the mansion. The user selected finding the worker alive and frightened, then returning to the carnival with every ride still available. Decisions are recorded in `Docs/FIRST_DEMO_DESIGN.md`; the proposed controller layout and operation requirements are in `Docs/CONTROLLER_AND_RIDE_CONTROLS.md`. The 15–20 minute estimate applies only to the core story proposal; the overall first demo also includes all discussed worlds, gameplay systems, rides, and the slums/hospital branch, and has no measured total duration.

This checklist comes from the current source, setup scripts, integration records, and saved validation reports. An unchecked item can mean unfinished implementation or missing end-to-end verification; it does not automatically mean that no supporting assets exist. The hospital branch was added after the earlier audit and is included below. No new gameplay or packaging tests were run for this audit.

**Already established**

- The mansion and coastal approach are connected to the carnival through always-loaded sublevels.
- The 1,028-metre route passed a complete movement test: about 3:50 at the player's normal movement speed, and 2:41 by motorcycle at the cautious test throttle. The slower walk modifier takes longer.
- The saved route passed 570 sampled floor/clearance checks with no blocking obstructions. This is not an audit of every accessible room or every place a player can leave the route.
- The doll has a 26-bone rig, 31 animation clips, reusable retargeting assets, and a tested approach/chase/scare/return system. One instance is placed beside the carnival haunted-house queue.
- The native editor build and controlled doll/route tests passed. The route tests used movement APIs and excluded the crowd spawner in an unsaved test world; hardware input, populated-scene performance, and a packaged demo are not established by those results. Automated doll tests did not audition audio.
- The opposite-side industrial branch is connected through nine sublevels, with a 1,536 m road, slum district, hospital exterior and interior, and six audio cues. The editor capture loaded the expected levels without errors. The previews are overexposed, and PIE traversal/exploration has not been accepted.

**Work remaining, in implementation order**

1. **Define the mission and its finish condition.**
   - [ ] Select the music-box prop, clues leading to the living/frightened worker, required mansion rooms, and scripted scare sequence; implement the return to carnival free play.
   - [ ] Implement explicit states for mission start, mansion arrival, item recovery, encounter, escape, and completion.
   - [ ] Make the objective understandable on screen and ensure it can finish using either walking or motorcycle travel to the house.

2. **Produce an early Windows development package.**
   - [ ] Build the runtime game target and cook the selected carnival world, lighting, connected sublevels, characters, and referenced assets.
   - [ ] Resolve runtime plugin, missing-reference, shader, and editor-only dependency failures before adding more content.
   - [ ] Confirm the executable launches directly into the intended starting experience. A successful editor build is not proof of a successful package.

3. **Implement full controller support and fix the real player controls.**
   - [ ] Reset motorcycle throttle, steering, and brake on input completion/cancellation and on relevant possession/menu transitions. The current native bindings handle `Triggered` only, while the bike retains the last values.
   - [ ] Fix braking while throttle is held; the current arcade branch applies braking only when throttle is neutral.
   - [ ] Add collision-safe motorcycle dismount placement and reliable recovery if the vehicle becomes stuck or overturned.
   - [ ] Implement and validate the proposed GTA V-inspired controller layout, starting with DualSense. Preserve analog stick movement, steering, and trigger acceleration/braking, with stick camera behavior independent of frame rate.
   - [ ] Validate the actual Windows controller backend and intended wired/wireless connection modes in a packaged build. Test additional supported modern controller families; do not infer hardware compatibility from generic button mappings alone.
   - [ ] Add device-appropriate button prompts, saved remapping, sensitivity/inversion/dead-zone settings, sprint hold/toggle options, vibration settings, controller reconnect handling, and clean keyboard/controller switching.
   - [ ] Test actual controller and keyboard/mouse inputs through movement, camera, sprint, jump, interact, mounting, driving, reverse, braking, dismounting, rides, operator consoles, all menus, pause, and resume. The complete game must be usable without keyboard/mouse after launch.

4. **Build the mission interaction flow.**
   - [ ] Implement the doors, object pickup, clues/keys, and locked/unlocked feedback actually required by the mission.
   - [ ] Give interaction prompts a clear focus/priority so a nearby activity, motorcycle, and mission item do not compete for the same key.
   - [ ] Prevent duplicate pickups, sequence skipping, and mission items becoming inaccessible. Keep the inventory as small as the chosen objective requires.

5. **Stage the mansion doll encounter.**
   - [ ] Place and configure a doll instance in the connected mansion; the existing placed instance is at the carnival haunted-house queue.
   - [ ] Author the reveal, stiff/twitchy movement, scripted approach/lunge, scare timing, sound, and aftermath.
   - [ ] Connect the scare event to mission progress without damage, death, or a catch/retry state. Gate the existing autonomous chase behavior off for the demo instances.
   - [ ] Test repeat encounters, approaching from either direction, escaping sight, leaving the house, and returning. Avoid accidental scares before the intended mission stage.

6. **Add gentle recovery, restart, and a story ending.**
   - [ ] Restore a consistent player position, objective state, doors/items, doll state, and motorcycle position when retrying.
   - [ ] Provide recovery from water, falls, inaccessible terrain, and a stuck vehicle without using the editor or console.
   - [ ] Clearly mark story completion and support the chosen continuation/free-play flow, replay, and quit. Scares must not cause failure; manual restart and technical recovery still need to work.

7. **Make the mansion's playable rooms work.**
   - [ ] Check player and camera clearance on stairs, doorways, landings, furniture, and the selected escape route.
   - [ ] Make required doors usable and visibly close off rooms that are outside the demo.
   - [ ] Verify floor/wall collision, item reachability, lighting readability, and the motorcycle parking/dismount area at the entrance.

8. **Verify navigation and encounter boundaries.**
   - [ ] Build or validate navigation for the mansion, its grounds, and carnival NPC areas, including stairs and door transitions used by the encounter.
   - [ ] Test the doll's scripted movement around furniture and corners with real player movement. Keep the player's path usable throughout each scare.
   - [ ] Keep the doll and carnival guests in their intended areas and prevent NPCs from blocking mission doors or trapping the player.

9. **Finish the coastal journey as a playable sequence.**
   - [ ] Test the route both directions, at ordinary walking/running and practical motorcycle speeds, including braking and turning on the bridge.
   - [ ] Check bridge edges, water access, off-route terrain, terrain seams, and alternate approaches beyond the already-tested centreline.
   - [ ] Tune signs, landmarks, sound, and a small number of suspense beats so the 3-5 minute normal-speed trip has a purpose.
   - [ ] Preserve seamless travel. Disable the demo's F-key map shortcuts or redirect them deliberately: F2 currently opens the separate source mansion map.
   - [ ] Accept the opposite-side industrial route in PIE on foot and by motorcycle: verify road collision, slum travel, transitions, and safe vehicle dismounts.
   - [ ] Correct the washed-out slum, hospital approach, and interior views while preserving Carnival night and worsening weather toward the hospital.
   - [ ] Verify factory-facade and entrance alignment; traverse the complete hospital interior and check doors, collision, lighting, audio, and access to all intended rooms.
   - [ ] Cook and test the hospital sublevels and their local asset dependencies in the standalone Windows build. The hospital's role in the story still needs design.

10. **Finish the characters and animation transitions that appear in the demo.**
    - [ ] Inspect player locomotion, jump/land, motorcycle mount/ride/dismount, and interaction animations on the actual player mesh.
    - [ ] Check retarget scale, foot sliding, hand contact, clothing/dress intersections, and animation transitions for every selected doll action.
    - [ ] Complete the discussed adult and child character roster. Verify skeleton compatibility, proportions, navigation capsules, clothing, and seated poses for each character used.
    - [ ] Integrate and validate the discussed animation content for the first demo, including retargeting, transitions, contacts, and runtime costs. The doll rig and retargeter already exist.

11. **Prove the carnival crowd works during gameplay.**
    - [ ] Validate the actual placed crowd spawner, built collections/outfits, walking behavior, navigation, and representation changes near the player.
    - [ ] Choose a crowd density that stays within the target machine's frame-time and memory budget.
    - [ ] Include the required ride staff in the character/performance budget and keep essential attendants independent of roaming crowd spawning/removal.
    - [ ] Run the complete mission with the intended crowd enabled; the successful route test excluded it.
    - [ ] Confirm guests do not collect mission objects, collide excessively with the player, or obstruct motorcycle access.

12. **Make every carnival ride usable by the player.**
    - [ ] Inventory all placed rides in the playable carnival and its runtime lighting sublevels; include repeated placed instances and record completion per ride.
    - [ ] Assign a visible attendant and suitable work/standby/boarding locations to every operating attraction. Keep every station covered throughout the missing-worker story.
    - [ ] Implement attendant-driven queue/boarding, actual start/stop commands, ride monitoring, controlled return, and unloading. Match staff gestures to real ride state and support a player-only cycle without waiting for a full crowd.
    - [ ] Select staff characters/clothing and prepare the needed greeting, directing, control-panel, monitoring, and unloading animations; verify floor/contact alignment and clear boarding/exit paths.
    - [ ] Complete seat placement, passenger offsets, hand/foot contact, queue flow, player boarding, motion/reactions, unloading, and a safe exit position for every seated ride.
    - [ ] Prove each complete ride cycle, player controls/camera, safe return to on-foot movement, and repeat use. All rides are required; a single featured ride is only an implementation starting point.
    - [ ] Implement Bumper Cars driving/arena interaction and the intended entry/experience/exit for walk-through or show attractions.
    - [ ] Add controller-operated start, controlled stop/return, and any appropriate speed/intensity settings at meaningful operator stations. Keep every ride accessible to a solo player as a passenger too.
    - [ ] Implement attendant-to-player operator handover and automatic staff resumption when the player leaves, with one active command source and no abandoned passengers or duplicate cycle starts.
    - [ ] Test attendant coverage, full operation, repeat cycles, and handover/resumption for every ride, both before and after returning from the mansion.
    - [ ] Reconcile existing integration with current assets: records show Swing seats created, other seat/exit tuning outstanding, and Ferris Wheel/Carousel/Bumper Cars lacking complete integration. Verify those records before assuming all rides work.

13. **Finish lighting and visual continuity.**
    - [ ] Reduce the remaining strong glare on mansion approaches/elevated views and make the mansion's playable rooms readable.
    - [ ] Match sky, fog, exposure, weather, water, and lighting across carnival, wetlands, and mansion.
    - [ ] Inspect terrain joins, floating/intersecting props, foliage clearance, material problems, and camera clipping from normal player viewpoints.

14. **Complete and audition the audio.**
    - [ ] Mix carnival ambience, wetlands wind/water/bridge sounds, and mansion atmosphere with smooth spatial transitions.
    - [ ] Verify footsteps, motorcycle sounds, door/item interactions, doll movements/laughs, and scare cues during real play.
    - [ ] Add usable volume controls and subtitles for any meaningful spoken content. Automated runs with audio disabled cannot verify the mix.

15. **Finish the player's interface.**
    - [ ] Provide start, pause/resume, retry, quit, objective display, and contextual control/interaction prompts.
    - [ ] Wire and test the settings interface, cursor/input focus, sensitivity, audio, and basic graphics options. Native settings hooks and a basic HUD already exist; the complete front-end flow is not verified.
    - [ ] Make text readable at supported resolutions and provide practical camera-shake/motion settings. Save settings between launches.
    - [ ] Make every menu, setting, confirmation, objective/clue screen, ride interface, and operator control work with controller focus, confirm/back navigation, and correct button prompts.

16. **Complete every discussed player-facing feature.**
    - [ ] Remove development travel/build/weapon shortcuts from the demo control scheme unless they are deliberately supported.
    - [ ] Do not expose unfinished movement as a promised feature: native ladder climbing is a stub; vault/mantle completion and clearance need end-to-end verification.
    - [ ] Complete every discussed activity, including start, finish, retry, cancel, scoring, and target resets. Current collectible overlap accepts any character, and target scoring lacks an active-activity guard.
    - [ ] Implement full combat with actual hit/damage behavior and feedback. The native weapon attack currently plays montage/audio only; define how combat fits the story and non-failing scripted scares.
    - [ ] Include building, advanced parkour, boats, hovercraft, advanced motorcycle stunts, and additional physics modes; finish their controls, feedback, recovery, and acceptance tests. The current arcade ramp code clears its launch velocity immediately.

17. **Profile and stabilize the full scene.**
    - [ ] Select the target PC specification and frame-rate target, then measure CPU/GPU frame time, RAM, VRAM, loading, and hitches with crowds, rides, motorcycle, lighting, and doll active.
    - [ ] Tune character/groom/outfit LODs, foliage, shadows, culling, texture streaming, and crowd density. Use distance-based world loading if measurements show the always-loaded areas are too costly.
    - [ ] Profile the existing `r.RDG.ParallelExecute=0` crash workaround; it can increase CPU rendering time. Confirm stability over repeated full runs.
    - [ ] Investigate coastal spline-construction warnings and material compatibility issues; fix those that affect runtime behavior, packaging, or stability.

18. **Build and test the distributable demo.**
    - [ ] Cook only needed maps and dependencies, set project/build metadata, include prerequisites as appropriate, and produce a clearly named Windows build.
    - [ ] Test launch and the complete mission on a machine without the editor, including cold loading, audio, settings, replay, and exit. Complete a controller-only pass with DualSense and repeat for other supported controller families/connection modes.
    - [ ] Have fresh players complete the objective and use every ride without spoken guidance. Record confusion, bugs, performance problems, and whether the intended horror pacing works.
    - [ ] Repeat after fixes until story completion, all rides, manual restart/recovery, and both travel options work reliably, with no scare-driven failure.

19. **Protect the project and prepare handoff.**
    - [ ] Back up the local licensed maps/models/animations, MetaHuman/crowd content, and Blender authoring sources in suitable private storage.
    - [ ] Preserve important files currently under `Saved` separately from disposable generated data. GitHub currently excludes licensed world/doll assets and is not a complete project backup.
    - [ ] Record required asset packs, regeneration steps, exact build version, tester controls, and applicable credits/attributions.

**Additional discussed scope now included in the first demo**

- Connect and make playable the previously discussed Town, Lighthouse, Castle, Arena, and Mars locations, with their intended travel links and complete play flows.
- Include the discussed adult/child character roster and animation content alongside every Carnival ride.
- Include full combat, extensive parkour, building, boats, hovercraft, advanced motorcycle stunts, and additional physics modes.
- Include the discussed larger inventory, long campaign, and multi-slot save system. Their detailed content, design, and acceptance criteria still need specification.

These items were previously described as deferred; the user's latest direction brings them into the first demo. Existing code/assets do not establish that their player-facing systems are complete.

**Acceptance test**

A new player can launch a packaged Windows executable and use a controller alone to play the full first-demo scope: Carnival, coastal wetlands/bridge, mansion story, industrial slums and explorable hospital, plus Town, Lighthouse, Castle, Arena, Mars, and the other discussed systems. They can use every ride with attendants, applicable operator controls, combat, parkour, building, boats/hovercraft, motorcycle features, the full discussed character/animation roster, long-form story, inventory, and save slots. The missing-worker/music-box story ends with the worker found alive and the player able to return to Carnival free play; scripted scares never cause death or failure. Restart, quit, safe recovery, keyboard/mouse use, intended NPC population, visuals, audio, and the agreed performance target all work in the packaged build.

**Audit references**

- `Docs/HAUNTED_MANSION_CONNECTION.md` and `Saved/MansionConnection/Route_Validation.json`, `Route_Playtest.json`.
- `Docs/HAUNTED_DOLL_IN_UNREAL.md` and `Saved/HauntedDollIntegration` reports.
- `Docs/CARNIVAL_INTEGRATION_STATUS.md` and the ride/crowd integration documents in `Plugins/CarnivalMetaHumanKit/Docs` (some sections are historical).
- `Source/CarnivalGame/CarnivalPlayerController.cpp`, `CarnivalPlayerCharacter.cpp`, `CarnivalMotorcycle.cpp`, `CarnivalWeaponBase.cpp`, `CarnivalActivityBase.cpp`, and `CarnivalTargetActor.cpp`.
- `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`, and `CarnivalGame.uproject`.
