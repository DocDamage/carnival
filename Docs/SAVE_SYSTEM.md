# Current save/load implementation

The pause menu is opened with Escape or controller Options/Menu. Use arrows or
D-pad to select, left/right to select one of three slots, Enter/Cross/A to choose,
and Escape/Circle/B to cancel or resume. Saving, loading, investigation retry and
quit have confirmations. A held confirm cannot accept its own confirmation.
Settings returns to the pause menu without briefly resuming the world.

Each slot has two alternating `.sav` generations under Unreal's platform save
directory. The newest structurally compatible generation is read from disk.
Saving writes the older bank and verifies it by reloading before reporting
success. A failed write retains the newest previous bank; failed verification
discards the attempted bank. Tests use unique namespaces and remove only their
own save files.

Version 1 persists:

- Persistent-world package identity, with PIE prefixes removed.
- Standing player transform and view rotation.
- Stable missing-worker mission stage. Carried key/clue/worker/music-box flags
  are reconstructed from that guarded stage and notify the placed story actors.
- Music-room door states keyed by level package plus actor name.
- Player-placed building mesh paths and transforms, with a maximum of 2,000
  pieces in a save. Only meshes in the current authored building palette load.

Save and load currently require standing on permanent walkable ground, outside
rides, vehicles, active activities, parkour, crouch/prone and the transient doll
scare. Load requires the same persistent world and all saved door actors.
Player floor and capsule clearance, saved door poses, building support and
clearance are checked before replacing current construction/progress. Building
replacements are staged and removed on failure. Successful load stops movement
and refreshes the player's recovery anchor at the restored position.

Native tests exercise three independent slots, camera/story/building/door
restoration, consumed-clue notification, older-bank recovery after an
incompatible newest generation, invalid slots/stages, falling/scare guards,
blocked saved positions and unavailable construction meshes. Input tests cover
controller menu navigation, held-confirm rejection, cancellation, keyboard
resume and settings round trips. These are software events, not hardware input.
Six production-HUD menu/confirmation captures have been visually inspected at
1280×800, 800×600 and 640×480. The render process exits cleanly on DX12.

This does not finish the full save requirement. Larger inventory and long
campaign content, equipment, vehicle transforms/modes and retry baselines,
additional relevant world state, cross-map opening/loading, packaged relaunch,
and physical controller acceptance remain to implement or verify. The
two-generation structural fallback is not a checksum or proof against every
possible file corruption. Future schema migrations must be explicit; version
mismatches currently reject that generation and try the older one.

## Version 3 (September 30, 2026)

The campaign dropped five out-of-scope stations, so saves are now version 3. Version-2 slots load through `UCarnivalCampaignSubsystem::MigrateVersion2`; version 1 still loads as before. Details: [CAMPAIGN_AND_INVENTORY.md](CAMPAIGN_AND_INVENTORY.md).
