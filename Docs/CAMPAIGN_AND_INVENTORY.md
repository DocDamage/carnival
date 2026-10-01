# The Signal Network

Authored under the user's September 30 instruction to link the campaign and inventory across all required locations. This document specifies the sequel to the existing missing-worker investigation. Native progression, transactions, inventory limits, journal, controller menu navigation and save migration are implemented; world placement, complete encounters, physical travel and presentation still require authoring and acceptance.

Eli's rescue remains the opening chapter. The player follows the notice board, wet glove, study log and service key to Eli and the music box, survives the harmless doll encounter, and returns to the Carnival. Eli's hospital recovery reveals the tide-powered service network behind the music-box signal. The sequel follows its broken lines, recovers its missing core and closes the signal loop. Eli and the four child guests remain safe; story scares never inflict damage or cause mission failure.

| Chapter | Locations and objectives | Progression item |
| --- | --- | --- |
| After the music | Hospital reception visiting pass → ward account → records-room utility chart | Visiting pass → Eli's account → utility chart |
| The broken line | Wetland survey route → railroad bridge relay → industrial-slum workshop ledger | Survey record → feeder tag → repair ledger |
| Beneath the surface | Prison archive and paintings → Research Lab A calibration → Lab B chart | Research access record → receiver sample → outfall chart |
| The tide road | Sewer outfall route → North Docks register → East Docks dispatch → shipwreck manifest | Landing record → register → wreck locator → tide manifest |
| The quiet engine | Atlantis core cradle → Lab B remote relay calibration | Tide core → remote authorization |
| Home again | Mansion receiver → Carnival service board | Restoration seal → permanent Carnival keepsake |

The hospital uses reception, a ward and the records room for the campaign, while the complete intended interior remains part of the explorable world. Both docks have distinct shipping evidence and a watercraft journey. Lab A measures the tide signal; Lab B charts it and later calibrates the recovered core at its remote relay. Combat never bypasses clues or damages Eli, the doll, children, attendants or guests.

Native stations have stable IDs in `UCarnivalCampaignSubsystem::Stations()`. Evidence stations accept inspection. Relay stations require three controls in the order stated in the objective. Wetland survey and sewer stations require three ordered route markers. A wrong control resets the partial sequence without consuming anything. A load safely restarts an incomplete sequence; completed stations stay completed. Physical marker placements must force the intended route, with clear, reachable return paths. Current native transactions do not establish those placement or traversal properties.

Each successful station exchanges the previous quest item for the next item and records its account in the journal. Earlier evidence remains readable in the journal. Quest items cannot be dropped, sold, duplicated or spent as general supplies. The ending grants one keepsake and leaves free play available. Replaying the original missing-worker investigation preserves the sequel, supplies and construction; starting a new complete campaign will need a separate explicit new-game flow.

## Scope change and version-3 saves

On September 30, 2026 the user removed Town, Lighthouse, Castle, Arena and Mars from the demo. Their five stations (town archive, lighthouse beacon, castle clock, Arena circuit, Mars relay) are gone, leaving 17. The slums ledger now points straight to the prison archive, and the Atlantis core is calibrated at Lab B's remote relay before the mansion receiver. Station IDs and rewards that remain are unchanged.

Saves are now version 3. A version-2 slot counted progress through the old 22-station order. On load, its completed count maps to the kept stations it covered, and a token from a removed station (keeper's code, clock seal, transfer entry, calibration or resonance record) becomes the item the next kept station expects. For example, a slot that had finished the lighthouse resumes at the prison holding the repair ledger. Supplies are unchanged. A wrong, missing or duplicated legacy token rejects the slot and leaves current progress untouched. Native regression tests cover each mapping and a full version-2 slot load.

## Inventory

Eight supply slots hold one stack per known item type. Quest tokens use separate reserved storage and cannot be blocked by a full supply bag. A grant succeeds completely or leaves the bag unchanged. Spending rejects unknown items, negative amounts, insufficient quantities and quest items.

The opening investigation's glove, study log, service key and music box appear in the bag from the existing mission state. Their use and retry behavior remain controlled by that state, avoiding conflicting copies of the same clue in two save systems.

| Supply | Stack limit | Intended use |
| --- | ---: | --- |
| Tickets | 9,999 | Activity rewards and supply-counter exchanges |
| Timber | 20 | Construction |
| Steel | 20 | Construction and sturdy repairs |
| Repair kit | 3 | Vehicle maintenance |
| Fuse | 5 | Optional service-panel repairs |
| Rope | 2 | Optional recovery and construction |
| Medical kit | 3 | Recovery in voluntary combat activities |
| Battery | 4 | Optional portable equipment |

Supply grant/spend transactions exist. Activity reward delivery, counters, pickup persistence, construction costs, vehicle repairs and medical-kit effects still need integration with their actual gameplay systems. The table defines their purpose; it does not claim these effects are already playable. Essential campaign relay repairs use reserved quest evidence and cannot be blocked by optional supply spending.

Inventory and campaign journal open from the pause menu using keyboard or controller. Left/right switches tabs, up/down changes entries, and Back returns to pause. Records wrap at the current screen width, with one journal entry per page. Five transient prototype screens were inspected, including an 800x600 journal record. Native simulated-input tests pass; complete-world presentation and physical controller acceptance remain open.

## Persistence and recovery

Save version 2 adds completed stations, sequel unlock state and inventory to the existing three-slot, two-bank system. It preserves story, camera, player position, construction and music-room doors. Invalid item IDs, duplicate stacks, overflow, missing quest tokens and impossible progress reject the snapshot. Version 1 remains readable: its original fields restore, the new bag starts empty, and a completed rescue unlocks the sequel. Failed location, collision or construction preflight must leave campaign and inventory unchanged along with the existing world/player state.

Campaign state lives in a game-instance subsystem, so legitimate map travel retains it. The current save loader still requires the saved map to be open; cross-map load orchestration remains required. Full package/cook, controller-only play, route signs, subtitles/audio, recovery, rewards and 30 FPS minimum / 60 FPS target acceptance remain open.

The sequel unlock is retained immediately after a safe rescue or completed-story restore. Replaying the opening investigation before visiting the hospital therefore cannot remove hospital access. That edge case is covered by the native regression suite.

The connected-world survey reads 18,047 loaded actors across 28 levels without changing the saved root map. Three draft hospital approaches have ground support and clear player-capsule space. These probes do not establish room designation, prop placement, sight lines during play or continuous return routes; all remain prerequisites for production station placement.

The three hospital stations are now placed in `L_IndustrialHospitalSetDress`: reception and ward focus their information boards, and the records station sits on the centre of the records desk top. That desk's pivot is a floor-level corner, so a native focus trace to it passes through chairs and the counter. Approach preflight (floor, capsule, sight line) passes for all three. In PIE, each station passes from its approach: the distance guard, the story gate, native focus, ordered context dispatch, the item exchange and the repeat guard. Only the set-dress sublevel was saved, with a backup; the persistent map hash is unchanged, and a fresh reload matches ids, radii, targets and positions. The ward approach is 3 m from its board (367 cm radius). These checks teleport the player; walked routes, rendered prompt readability, physical controller input and cooked play remain open. Evidence: Saved/CampaignAcceptance/HospitalStationApproachesDiagnosed_20260930, HospitalRecordsDeskTopFocus_20260930 and HospitalStationsAuthoredDeskTop_20260930.

## Station placement status

All 17 stations are placed in the connected world. One PIE proof of the whole campaign completes every station in order through the real character's native context interaction, with none advanced through the API alone. Distance, wrong-order (sequence stations) and repeat guards hold, and the ending keepsake is awarded once.

| Station | Placement |
| --- | --- |
| Hospital reception, ward, records | Info boards and the records desk |
| Wetlands markers 1–3 | Numbered poles beside (not on) three Carnival–bridge wetland route segments |
| Bridge relay 1–3 | Three switch boxes beside the bridge's west threshold, off the route surface |
| Slums workshop | Desk with the repair ledger at the slums' hospital-side street interface, at least 6 m off the road's driving line |
| Prison archive | Archivist's desk with the ledger at the base of the Prison main tower |
| Lab A calibration 1–3 | Lab A's two displays and control panel on its raised platform |
| Lab B chart | Gallery portrait wall in Lab B's corridor |
| Sewer markers 1–3 | Numbered poles along the sewer corridor between the Prison stair and the Atlantis passage |
| North Docks register, East Docks dispatch | Desks with records beside each dock's spine endpoint (North) and on the East Dock main quay, off the approach |
| Shipwreck manifest | Chest on the wreck floor |
| Atlantis cradle 1–3 | Three ruin columns in the central hall |
| Lab B remote relay 1–3 | Lab B's two displays and control panel |
| Mansion receiver 1–3 | Three switch boxes in the foyer hall |
| Carnival service board | Service board at the Carnival's wetlands-side entrance |

Every placement was chosen by `Scripts/find_campaign_station_sites.py`. A standing spot must be reachable by a step-aware collision flood from the region's connection anchor (1 m grid, 50 cm in the labs). It needs a clear capsule and a clear native focus trace, and for fixtures an eye-level sight line that reaches the fixture itself. For three-control stations, its own control must be the nearest. Props are collidable static meshes in each region's own level. Station actors face their standing spots so the 1/2/3 labels read correctly.

The prison, Lab A and Lab B stations became reachable only after the world-expansion access repair: corrected sublevel rotations, Lab B alignment, and an opened Lab A west connector (see `Docs/WorldExpansion/LAYOUT_AND_CONNECTIONS.md`). The production character walked to and from the Lab A controls, Lab B chart, Lab B relay and Prison archive in PIE.

The Prison archive is a desk because the main-tower paintings are not readable from reachable ground. They hang about 6 m up and their canvases are not visible; this follow-up is recorded in the layout document.

Not yet established:

- travel between region anchors along R03–R08 and R10–R12
- in-game prompt and label readability
- physical controller input
- cooked play
- performance

Long PIE wall-clock times on some walks come from editor skinned-asset compilation under low memory (hundreds of `AssetCompile memory estimate` warnings), not from the routes.

Evidence: StationSites8/17, CampaignStationsAuthored2–4 (index, Reload.json, level backups), CampaignStationsRendered2/3, StationWalkPIE*, LabGateWalk3 and ExpansionAnchorConnectivityAfterRotationFix under `Saved/CampaignAcceptance`.

On 2026-10-01, station props standing on route surfaces were re-sited; the slums desk had blocked the R07 motorcycle route. The site finder now rejects prop sites on road, route, approach, walkway, crossing, driveway, forecourt or trail surfaces. Where the street itself is the road mesh (slums), it instead keeps props at least 6 m from the driving line. The sewer marker 3 pole remains on the walk-only sewer corridor floor. All 17 stations again pass the native-interaction PIE proof (`CampaignStationsAuthored5_20261001`), and the affected routes pass walking and motorcycle runs.
