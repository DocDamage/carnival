The demo is partly implemented, but not ready for release. Currently, 34 native tests pass, sampled cycles cover all 25 placed rides, several travel routes pass, and 240 crowd entities render. Full gameplay, appearance, controller, and packaged-build acceptance remain open.
This checklist covers the full demo scope you requested, including the additional worlds and systems. “Verify” means implementation exists but still needs real gameplay testing.
Build and launch
- [ ] Finish the packaged MetaHuman compatibility fixes and eliminate missing crowd assets and fallback materials.
- [ ] Fully recook the current content; the older package does not contain all recent changes.
- [ ] Verify every required map, character, animation, sound, and gameplay asset is included.
- [ ] Verify launch, loading, play, and clean exit on a Windows machine without Unreal Editor installed.
Playable world
- [ ] Finish and verify Carnival, wetlands, railroad bridge, mansion, industrial slums, and the complete intended hospital interior.
- Town, Lighthouse, Castle, Arena and Mars were removed from the demo scope by the user on September 30, 2026. Their vendor packs stay in the project but are not connected or required.
- [ ] Finish and verify North Docks, East Docks, Prison, both Research Lab rooms, Sewers, Atlantis Ruins, and Shipwreck.
- [ ] Test every connection in both directions with ordinary player movement and supported vehicles.
- [ ] Check all intended rooms, doors, stairs, ladders, landings, tunnels, entrances, and exits.
- [ ] Fix remaining terrain seams, collision gaps, invisible barriers, floating props, camera clipping, and places where players can become trapped.
- [ ] Establish safe water boundaries, shoreline access, parking, mounting, and dismounting areas.
- [ ] Add clear signs and landmarks, and replace development travel shortcuts with deliberate player-facing travel.
Several sampled mansion, hospital, Atlantis, and sewer routes already pass. Those checks need extending to the complete populated world.
Player and characters
- [ ] Finish the actual clothed player character and its materials.
- [ ] Verify walking, running, sprinting, jumping, landing, crouching, prone movement, swimming, and interaction animations.
- [ ] Finish motorcycle rider poses, including hand contact, foot contact, clothing clearance, mounting, and dismounting.
- [ ] Finish the adult guest, attendant, Eli, and doll appearances and animation transitions.
- [ ] Finish all four imported child characters: BlackGirl, BlackBoy, WhiteGirl, and WhiteBoy.
- [ ] Resolve remaining child mesh/material issues, including BlackGirl’s shirt appearance and BlackBoy’s skin, eyes, and pose intersections.
- [ ] Verify every used character’s proportions, capsule, feet, clothing, locomotion, seated poses, and animation transitions.
Crowd and attendants
- [ ] Implement actual guest roaming and navigation; spawning and rendering alone do not establish crowd behavior.
- [ ] Integrate child guests into the world with suitable movement and interactions.
- [ ] Verify crowd appearance and representation changes as the player approaches and moves away.
- [ ] Prevent guests from blocking doors, vehicle access, mission objects, queues, and exits.
- [ ] Give every operating attraction a recognizable attendant with appropriate clothing and animations.
- [ ] Keep attendants available through story completion, replay, recovery, and controller reconnection.
- [ ] Select the final crowd density from measured performance.
Every ride and attraction
Required families are Swing, Pirate Ship, Balloon Tower, Clown Ride, Flying Bobs, Circus, Haunted House, Hot Air Balloon, Teapot, Ferris Wheel, Carousel, and Bumper Cars.
- [ ] Verify all 25 placed instances, including Day, Night, and Snow variants.
- [ ] Check every usable seat/cabin/horse for attachment, character fit, clothing intersections, camera clearance, and safe exits.
- [ ] Verify attendant-run boarding, a complete cycle, controlled return, unloading, and repeat use.
- [ ] Support a solo passenger without requiring other guests to fill the ride.
- [ ] Finish guest queueing, occupied-seat handling, and passenger transitions.
- [ ] Verify applicable player operator controls and attendant handover/resumption.
- [ ] Verify Bumper Cars driving, arena boundaries, session completion, unloading, and reset.
- [ ] Finish the intended Circus and Haunted House experience, including entry and exit.
- [ ] Test every attraction before and after the story, using actual controller input.
The common ride logic and sampled cycles exist; complete seat, presentation, crowd, and hardware acceptance remain.
Vehicles and movement systems
- [ ] Verify motorcycle acceleration, braking, reverse, steering, camera, mounting, dismounting, and recovery on actual world terrain.
- [ ] Finish and verify advanced motorcycle stunts, wheelies, ramps, suspension, tipping, and the additional physics modes.
- [ ] Verify switching between arcade and Chaos motorcycle behavior without losing control or motion.
- [ ] Finish boat and hovercraft routes, boundaries, shore interactions, boarding, unloading, and recovery.
- [ ] Verify vaulting and mantling against the actual environment, including blocked landings and interrupted traversal.
- [ ] Place functional ladder markers and finish climbing animations, camera behavior, and entry/exit clearance.
- [ ] Verify movement, posture, combat, building, and vehicle transitions cannot leave controls or collision stuck.
Activities, combat, building, and inventory
- [ ] Author playable activities with clear objectives, starts, scoring, completion, cancellation, retries, and resets.
- [ ] Verify targets, collectibles, checkpoints, timers, and rewards in their actual world placements.
- [ ] Finish combat encounters, opponents, health behavior, animations, hit feedback, and player-facing controls.
- [ ] Define and implement combat’s relationship to the story and its non-failing scripted scares.
- [ ] Finish building selection, placement previews, valid-placement feedback, demolition, and persistence.
- [ ] Specify and implement the larger inventory: item acquisition, use, presentation, limits, and persistence.
- [ ] Complete the discussed campaign content and progression, with clear objectives and playable connections between locations.
Native foundations exist for several of these systems. Their complete authored gameplay is still required.
Missing-worker story and horror
- [ ] Play the complete notice board → foyer clue → study/key → Eli → music box → scare → Carnival return sequence without test teleports.
- [ ] Finish Eli’s safe side-route walk-away and verify he cannot obstruct the player.
- [ ] Finish the doll’s framing, animation contacts, lighting beat, blackout, lunge, sound, and aftermath.
- [ ] Verify scares cause no damage, death, failure, or trapped movement.
- [ ] Test unexpected approaches, leaving and returning, repeated interactions, and attempted sequence skipping.
- [ ] Verify readable objectives, clues, dialogue, and contextual interaction priorities.
- [ ] Verify both walking and motorcycle journeys, including safe mansion parking.
- [ ] Verify completion feedback, continued free play, and story replay.
- [ ] Define and implement the hospital’s intended narrative role.
Save, restart, and recovery
- [ ] Implement and verify the discussed multi-slot save/load system.
- [ ] Save and restore campaign progress, inventory, relevant world/building state, and player location.
- [ ] Ensure story retry consistently resets doors, items, Eli, doll, objectives, player, and motorcycle.
- [ ] Verify player recovery from water, falls, blocked paths, and other actual-world traps.
- [ ] Verify motorcycle and watercraft recovery without editor commands.
- [ ] Test loading, restarting, quitting, and relaunching from different gameplay states.
Controls and menus
- [ ] Verify the GTA V-inspired layout across walking, vehicles, passengers, operators, combat, building, and menus.
- [ ] Test DualSense on the intended wired and wireless Windows connections.
- [ ] Test each additional supported controller family and document the required input backend.
- [ ] Verify analog movement, steering, triggers, camera sensitivity, inversion, and dead zones.
- [ ] Verify saved remapping, sprint options, vibration settings, and device-appropriate prompts.
- [ ] Verify disconnect/reconnect behavior and keyboard/controller switching.
- [ ] Make the entire game usable with a controller alone after launch.
- [ ] Finish and test start, pause, resume, retry, save/load, settings, confirmations, and quit.
- [ ] Remove or simplify the large development HUD overlays currently obscuring gameplay.
- [ ] Verify text, scrolling, menu focus, and prompts at supported resolutions.
Visuals and audio
- [ ] Correct dark crowd silhouettes, excessive glare, washed-out areas, and unreadable interiors.
- [ ] Match lighting, exposure, fog, weather, and water across connected regions.
- [ ] Review all characters and clothing under actual gameplay lighting.
- [ ] Finish and inspect Prison paintings, Lab B art, glass, and other outstanding presentation details.
- [ ] Audition Carnival ambience, environmental transitions, vehicles, footsteps, interactions, dialogue, music-box motif, and scares.
- [ ] Verify attenuation, looping, transitions, volume persistence, and subtitles.
- [ ] Verify supported graphics and motion/camera settings.
Performance and final acceptance
- [ ] Establish the target PC specification and frame-rate target.
- [ ] Measure CPU/GPU frame times, RAM, VRAM, loading, and hitches with the complete populated world.
- [ ] Tune character LODs, grooms, clothing, foliage, shadows, textures, crowd density, and world loading.
- [ ] Resolve consequential remaining cook/runtime warnings and confirm repeated-run stability.
- [ ] Complete a packaged controller-only pass through the story, every ride, all locations, and all gameplay systems.
- [ ] Repeat with keyboard/mouse, save/load, replay, recovery, and extended play.
- [ ] Have fresh testers play without spoken guidance; fix confusing objectives and reproducible failures.
- [ ] Prepare controls, build/version information, required credits, and known limitations.
- [ ] Back up licensed assets, authoring sources, and important local reports; GitHub currently does not contain the complete asset project.
The latest evidence is in [the completion record](F:/Carnival/Docs/COMPLETION_PASS_20260929.md). The [existing demo checklist](F:/Carnival/Docs/PLAYABLE_DEMO_CHECKLIST.md) contains older entries that must be read alongside those newer results.