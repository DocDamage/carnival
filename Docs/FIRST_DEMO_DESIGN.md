# First demo design — decisions and proposed details

This records the user's selected direction and clearly labels the details still proposed. It is not a record of implemented gameplay. On 2026-09-27, the user clarified that everything discussed for this project belongs in the first demo. This supersedes earlier wording that deferred discussed locations or systems.

**Confirmed decisions**

- Carnival, connected coastal wetlands/railroad bridge, and haunted mansion, with seamless walking and motorcycle access.
- A second road from the opposite Carnival gate goes through the industrial slums to the abandoned, fully explorable hospital. Keep the night setting and worsen the weather toward the hospital.
- All previously discussed project locations and gameplay systems belong to this first demo; none are deferred solely because an earlier note called them later milestones.
- Combine all three story elements: a missing carnival worker, an old music box, and unexplained lights/sounds at the mansion.
- Scripted doll scares only, with no death or failure condition. The doll's movement style stays stiff and twitchy.
- A small lively midway that gradually feels ominous.
- **Every carnival ride must be usable in the demo.** A single featured ride or scenery-only substitutes do not satisfy this requirement.
- Every operating ride must have an assigned NPC attendant who actually manages boarding, operation, and unloading.
- The missing worker is found alive and frightened inside the mansion.
- After the mansion sequence, return to the carnival and continue using every ride.
- Include separate ride-operator controls where they make sense for the attraction. Ordinary passenger use must remain available for every ride.
- Full modern controller support is required, with movement, camera, interaction, and vehicle controls reminiscent of GTA V.
- PlayStation 5 DualSense is the user's first test controller for the Windows demo.

**Ride operation and controller decisions**

The user selected operator controls, qualified by whether they suit the ride. Use meaningful control stations for applicable motorized rides, with start, controlled stop/return to loading, and only supported speed or intensity settings. Bumper cars are directly driven. Walk-through/show attractions receive controls only for mechanisms or show functions that actually exist. A lone player must be able to enjoy every ride without having to remain at an operator console.

NPC attendants are the default operators. Each attraction has an assigned attendant at its boarding area or control station. The attendant manages the queue, admits riders, starts the actual mechanism when boarding is complete, monitors the cycle, returns it to the unloading position, and releases passengers. At suitable player-operable rides, the attendant hands over control, steps aside, and resumes when the player leaves the console. Passenger and player-operator modes must both work while the attendant is present.

Recommended casting: use adult staff from the available character assets, with recognizable staff clothing and a small set of idle, greeting, boarding, button/lever, monitoring, and unloading gestures. Make the missing person a maintenance worker, or provide explicit cover for their station, so every ride remains staffed during the mansion story and after the player's return.

The proposed DualSense/Xbox layout, controller support requirements, and per-attraction operation rules are recorded in `Docs/CONTROLLER_AND_RIDE_CONTROLS.md`. These requirements include all menus, settings, riding, operator consoles, and the complete story. Controller support is a release requirement, not an optional test.

Recommendations below remain proposals where the user has not selected the detail. Silence is not approval.

**Recommended experience**

The player begins at a still-operating carnival near closing time, with every ride staffed and available to use. A maintenance message explains that a worker went to the old mansion to retrieve a music box for the haunted-house attraction and has not returned. Reports of lights and music from the supposedly empty house give the player a reason to investigate.

The carnival's noise fades along the wetlands route, which can be travelled on foot or by motorcycle. Distant lights and the music-box melody draw attention toward the mansion. Inside, a short trail of the worker's belongings or notes leads through a few rooms. The player finds the worker alive and frightened, then retrieves the box near a seated doll. Recovering the box triggers a staged reveal: a head snap, a sudden change of position while out of view, or a brief lunge with sound and lighting. The player can continue safely; the sequence does not become a chase or catch-and-retry loop.

The opposite-side industrial branch is also first-demo content: players can leave the Carnival, travel through the slums, and explore the abandoned hospital interior. Its narrative connection to the missing-worker investigation has not yet been selected; preserve it as a complete explorable branch while that story role is designed.

The investigation resolves by finding the worker and recovering the box. The player returns to carnival free play, with every ride still available. Recommended staging: the worker leaves independently and is present at the carnival on return, avoiding a mandatory escort. A small final audio cue can suggest that the haunting followed the box without locking rides or starting a new failure sequence.

The music-box prop, melody, worker character, and exact mansion rooms still need selection. The three story elements form one investigation and one objective chain rather than three separate quests.

**Proposed pacing, to be measured in playtests**

| Segment | Proposed time | Player experience |
|---|---:|---|
| Carnival opening | 2–3 minutes | Learn movement/interact, learn about the missing worker, find the trail and optional motorcycle. Every ride is usable; riding is optional to the story. |
| Wetlands and bridge | 3–5 minutes on foot | Follow existing signs, hear the carnival fade, experience one distant unexplained event. |
| Mansion exploration | 4–6 minutes | Follow the worker's clues and the music through a few rooms, use one simple interaction, find the box and doll. |
| Scripted scares and resolution | 1–2 minutes | Experience the doll reveal after finding the worker alive, and leave safely with the box. |
| Return journey | Mode-dependent | Travel back to carnival free play using the same seamless route and chosen travel mode. |
| Industrial slums and hospital | Additional exploration | Current route estimates are about 5:41 on foot or 4:00 by cautious motorcycle to the hospital door; full interior exploration time is unmeasured. |
| Other discussed locations and systems | To be scoped and measured | Town, Lighthouse, Castle, Arena, Mars, and all other discussed gameplay systems are included in this first demo. |
| Carnival rides and exploration | Open-ended | Every ride is usable and repeatable; total play time grows with the rides the player chooses. |

The core missing-worker story can target roughly 15–20 minutes including a return journey; this is a design target to measure, not the length of the full first demo. The slums/hospital, all rides, and other discussed locations and systems add play time. The 3–5 minute route target is for normal-speed travel on foot; motorcycle travel is naturally shorter. The existing approximately 3:50 foot test is evidence for the coastal route only, not a measured mission length.

**Recommended defaults for the remaining decisions**

| Decision | Recommendation | Reason |
|---|---|---|
| Player camera | Keep third person; tune mansion camera collision. | Reuses the current character/controller and shows the character and motorcycle animation work. |
| Story delivery | A short opening message, two or three worker clues, concise objective updates, and a worker-outcome scene. | Makes the combined mystery understandable without requiring long cinematics. |
| Mansion size | One selected route through approximately 3–4 rooms, with unfinished areas visibly closed. | Makes the house navigable and gives the encounter a layout that can be thoroughly tested. |
| Puzzle | One simple clue-and-key or clue-and-interaction obstacle, with nearby feedback. | Gives exploration a purpose without turning the demo into an inventory system. Choose the specific interaction after inspecting the selected rooms. |
| Doll presentation | Begin seated and apparently inert; build toward a head snap, an out-of-view position change, and one close reveal. | Implements the selected scripted-scare direction and possessed-doll style. |
| Doll control | Drive the demo instances from mission triggers and gate the existing automatic chase behavior off. | Existing chase capability remains reusable, but the demo must respect the user's no-failure choice. |
| Failure | No death, catch penalty, mission timer, or mandatory scare retry. Keep the path usable and prevent scare animations from trapping the player. | Confirmed user preference. Environmental mishaps still need gentle recovery. |
| Recovery | Safe repositioning for a stuck player/vehicle; restore consistent mission state on manual restart. | Technical recovery should not introduce a punishment loop. |
| Combat | Include the combat system discussed for the project; define its encounters, feedback, controls, and relationship to the story and scripted scares. | The user's latest scope clarification supersedes the earlier recommendation to omit combat. |
| Motorcycle | Optional travel, with obvious parking outside the mansion and reliable recovery/dismount. | Both travel choices remain viable; the house is explored on foot. |
| Crowd | Start with a small tested population; choose the final count from performance measurements. | The full crowd has not been validated in the combined scene. |
| Child characters | Include the discussed character roster as demo content; verify rig, animation, collision, clothing, navigation, and performance for each character used. | The latest scope direction includes all discussed character content; readiness and integration remain acceptance work. |
| Rides | Every ride in the playable carnival is usable by the player and repeatable. Build common boarding/ride/exit behavior first, then complete and test each attraction. | Confirmed user requirement. Existing NPC passenger components are not proof of player riding. |
| Ride operation | Separate operator controls where meaningful; ordinary passenger use remains available. | Confirmed user choice, with controls tailored to the ride's mechanisms. |
| Ride attendants | Assigned NPC staff run every operating attraction by default, handle boarding/unloading, and hand over/resume applicable player operator controls. | Confirmed user requirement for attendants running the rides. |
| Controller support | Full controller play, led by DualSense testing, with GTA V-inspired controls and device-appropriate prompts. | Confirmed user requirement. See the detailed input specification. |
| Ride access | Recommend free admission and clear interaction prompts throughout the demo, without ticket grinding or story prerequisites. | Lets testers try every ride directly. |
| Ride camera | Recommend player-controlled look from a stable seated camera, with restrained forced shake. | Lets players enjoy the motion and scenery while preserving readable controls. |
| Lighting | One consistent night setting with readable paths and interiors. | Keeps the lighting pass focused; no dynamic day/night feature is needed for this demo. |
| Audio | Use a recurring music-box motif, spatial ambience, and a small number of deliberate scare cues. | Supports wayfinding, mood, and the proposed story. Final assets and mix still need work. |
| Interface | Start, pause/resume, retry, quit, concise objective text, contextual prompts, basic settings. | Covers the complete standalone player flow. |
| Performance | Target scalable 1080p at 60 fps on the current PC, then measure and tune. | A target for profiling, not a performance claim or published minimum specification. |
| First testers | A small private Windows build for a few fresh players before a public release. | Finds confusing objectives and control failures before broader distribution. |
| Progress storage | Include the discussed long campaign, larger inventory, and multi-slot save system, with reliable mission/settings persistence. | These were previously deferred; the latest scope direction brings them into the first demo. Detailed requirements remain to be authored. |
| Ending | Complete the investigation and return to carnival free play with all rides available. | Confirmed user choice; show story completion without terminating free play. |

**All-ride completion requirement**

Current project records identify these ride/attraction categories: Swing, Pirate Ship, Balloon Tower, Clown Ride, Flying Bobs, Circus, Haunted House, Hot Air Balloon, Teapot, Ferris Wheel, Carousel, and Bumper Cars. Reconcile this list against every placed ride in the selected runtime carnival and its lighting sublevels; include any additional ride found. Test repeated placed instances, not just one asset per type.

For each ride, record its assigned attendant and station, player access/boarding, correct attachment to its moving seat or platform, seat/camera clearance, a complete attendant-run cycle, safe unload/exit, return of player movement/input, and repeat use. Test applicable player operator controls, attendant handover/resumption, and all these flows using the controller. Walk-through/show attractions need their intended entry, experience, and exit rather than an artificial seated interaction. Bumper cars need drivable vehicles, arena collision, and an attendant-managed session/end/reset flow. Integrate the small crowd without allowing occupied seats, queues, or staff to permanently block the player.

All-ride operation is a release requirement. The story's short duration does not reduce this requirement. Ride completion and full-scene performance testing will therefore be substantial parts of the demo work.

**Implementation sequence**

1. Prove an early Windows package and establish the controller foundation, including DualSense device input, prompts, menu navigation, analog movement/driving, and clean mount/dismount/context transitions.
2. Build common attendant-run boarding, ride operation, and unloading, plus applicable player operator handover; validate them on Swing, then finish and staff every other placed ride, including Bumper Cars and rides in the lighting sublevels.
3. Implement the combined mystery, minimal interactions, worker outcome, and story completion in the selected mansion rooms.
4. Stage the doll's scripted scares, including safe behavior when approached in an unexpected order or revisited.
5. Finish environment lighting, audio, selected animations, and the small population within a measured performance budget.
6. Package, test the whole story, all menus, every ride, and applicable operator panels using controller-only play; repair failures and repeat with final content enabled. Retest keyboard/mouse alongside controller hot switching.

All remaining implementation and verification tasks are tracked in `Docs/PLAYABLE_DEMO_CHECKLIST.md`. The user's latest scope clarification brings all discussed locations and systems into the first demo, including Town, Lighthouse, Castle, Arena, Mars, combat, building, advanced parkour, boats, hovercraft, advanced motorcycle stunts, additional physics modes, the discussed character/animation content, and expanded story, inventory, and save work. Detailed designs and acceptance criteria for those systems remain to be written.
