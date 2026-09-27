# Controller and ride controls — demo requirements

The user requires every carnival ride to be usable and run by an NPC attendant, additional player operator controls where appropriate, and full modern controller support with controls reminiscent of GTA V. **PlayStation 5 DualSense is the primary test controller.** This document specifies the intended result; the mappings and features below are not yet implemented or hardware-validated.

The layout is a proposed GTA-inspired arrangement for this game's actions, not a claim of exact parity with every GTA V binding. Preserve familiar stick movement/camera control, face-button running and jumping, triangle/Y entry and exit, and trigger-based driving. Use the same physical control positions across controller families where possible.

**Proposed default layout**

| Context / action | DualSense | Xbox equivalent | Behavior |
|---|---|---|---|
| On foot: move | Left stick | Left stick | Analog walking/jogging relative to the camera. |
| Look around | Right stick | Right stick | Adjustable horizontal/vertical sensitivity and optional inversion; frame-rate-independent stick rotation. |
| Sprint | Cross | A | Hold by default, with a toggle option. No required repeated tapping. |
| Jump | Square | X | Jump; contextual vaulting only after that feature is implemented and verified. |
| Enter/leave motorcycle; board/request exit from a ride | Triangle | Y | Contextual entry/exit. Ride exit waits for or returns to a valid unloading position. |
| Use door, inspect clue, collect object, enter operator station | D-pad right | D-pad right | One clear focused interaction, shown by an action-specific prompt. |
| Crouch | L3 | Left-stick click | Toggle crouch where allowed; provide remapping. |
| Vehicle: steer | Left stick X | Left stick X | Proportional steering. |
| Vehicle: accelerate | R2 | RT | Analog acceleration. |
| Vehicle: brake/reverse | L2 | LT | Brake while moving forward; transition deliberately to reverse at rest. |
| Vehicle: rear brake/handbrake where appropriate | R1 | RB | Distinct from ordinary braking; release reliably. |
| Vehicle: look behind | R3 | Right-stick click | Temporary rear view while held. |
| Pause | Options | Menu | Available on foot, driving, riding, and at consoles. |
| Objectives/help | Touchpad click | View | Accessible controller-operated screen; provide an equivalent mapping for controllers without a touchpad. |
| Menus: navigate | D-pad / left stick | D-pad / left stick | Visible focus, repeat-rate tuning, scrolling, and slider adjustment. |
| Menus: confirm / back | Cross / Circle | A / B | Consistent across menus, notes, settings, and operator panels. |
| Operator station: select / activate / back | D-pad / Cross / Circle | D-pad / A / B | Only supported operations are shown; direct-control levers can use an appropriate analog input. |

Keyboard and mouse remain fully supported. Keep E for ordinary interaction and use F for vehicle/ride entry if adopting the proposed separation. Escape pauses. Gameplay contexts must ensure that confirming a menu does not also sprint, activate a world interaction, or operate a vehicle.

**Controller support means the complete experience**

- Begin at the first in-game screen and play the story, ride every attraction, use applicable operator controls, change settings, restart, continue free play, and quit without reaching for a keyboard or mouse.
- Implement DualSense button prompts as the primary presentation, with Xbox and other supported layouts available. Change prompts when the active input device changes, avoid flicker from idle stick drift, and offer a manual icon override when a compatibility layer obscures the original controller type.
- Preserve analog stick and trigger values. Separate mouse-delta look from stick look rate, clamp diagonal movement, and tune inner/outer dead zones and response curves.
- Save remapping, look sensitivity, inversion, dead zones, sprint hold/toggle, vibration strength, and camera-shake preferences. Detect conflicting mappings and provide a controller-accessible restore-defaults action.
- Supply ordinary vibration where the device/backend supports it, with an off switch and adjustable intensity. Advanced DualSense trigger resistance or richer haptics require a separate backend/connection check before being promised as finished. Essential actions must remain usable without those effects.
- Test controller connection at startup, hot-plugging, disconnection/reconnection, keyboard/controller switching, and paused/resumed play. Clear stored throttle, steering, braking, sprint, and interaction holds when input is lost or the context changes. Pause the single-player game on controller loss and make recovery possible with either input method.
- Test native device input and any supported compatibility-layer path separately. Avoid double input when two paths expose the same physical controller.

DualSense is the first hardware test, with intended USB and Bluetooth validation. Xbox Series/One-compatible pads, DualShock 4, and supported generic/Steam Input pads belong in the wider compatibility matrix. Confirm each device/connection route in the packaged Windows build before marking it supported. The user has not selected a console release or required a Steam release by requesting controller support.

**Passenger and operator experiences**

Every ride remains usable by a solo player, with an assigned NPC attendant running it by default. Boarding is a normal passenger interaction. Where an attraction has a meaningful control panel, the player may also enter an operator mode through a clear handover from the attendant. The attendant steps aside and resumes when the player leaves. Operating a panel must not be a prerequisite that makes the player simultaneously occupy a seat and a distant booth.

The shared ride states should support loading, securing/boarding, running, controlled return/stopping, and unloading. Entry/exit prompts reflect the current state. A request to leave a moving ride brings it to an appropriate unloading state; it must not detach the player in midair. Exiting a console restores normal input and camera control without leaving a stale start/stop command active.

**Attendant behavior and control handover**

- Assign a visible adult attendant to each operating attraction/boarding station. One arena attendant can manage its bumper-car fleet; individually operated attractions need their own coverage. Reconcile repeated placed ride instances in the staffing inventory.
- The attendant acknowledges guests, manages boarding/queue progression, signals readiness, operates the control panel, monitors the cycle, and directs unloading. Gestures and any announcements follow the actual ride state.
- Start and stop commands must drive the vendor ride's actual mechanism and the shared gameplay state. A console animation or passive motion observation alone does not establish that the attendant runs the ride.
- Use one active command source at a time: attendant, player operator, or controlled handover. Preserve the current cycle across handover, stop stale held commands, and do not restart a cycle or detach passengers merely because control changes.
- A passenger never needs to leave their seat to start the ride. An empty queue must not force the player to wait indefinitely for more NPC riders; allow a bounded boarding window and a cycle with the player alone.
- In operator mode, show only actions valid for the current ride state. On leaving the console, the attendant resumes the current cycle or the appropriate loading state. Apply the same recovery to interrupted interactions and controller disconnect/resume.
- Put the attendant's working, standby, and approach locations clear of the loading/exit path. Keep staff separate from the roaming guest population so crowd changes do not remove an essential operator. Reduce distant visual detail without losing authoritative ride state.
- Staff remain assigned before, during, and after the mansion mission. Recommended story casting makes the missing person a maintenance worker; otherwise explicitly provide a covering attendant.
- Add recognizable staff presentation and selected idle/greet/direct/operate/watch/unload animations. Reuse or retarget existing clips where suitable, and author missing contact poses. Subtitle any meaningful spoken instructions and keep controller prompts sufficient on their own.

| Attraction family | Proposed usable experience | Operator controls where appropriate |
|---|---|---|
| Swing, Carousel, Teapot, Clown Ride, Flying Bobs | Board a valid seat, enjoy a complete cycle, unload, and repeat. | Start cycle; controlled stop/return; bounded speed presets only where the actual mechanism supports them. |
| Pirate Ship | Seated swinging cycle with correct passenger attachment and camera. | Start cycle; optional bounded intensity preset; settle to the loading pose before unloading. |
| Ferris Wheel | Board a cabin at its loading position, ride a cycle, return and unload. | Advance/index a cabin; start cycle; return to loading. Validate each cabin's attachment and boarding location. |
| Balloon Tower / Hot Air Balloon attractions | Use the placed attraction's intended ascent/rotation/return cycle. | Start/ascent and return/lower controls if supported by its mechanism; confirm the actual ride behavior before exposing controls. |
| Bumper Cars | The attendant admits the player, starts the arena session, and manages its end; the player drives a car and exits safely. | Player driving is the main control experience; an arena-session panel can be added if there is a useful role for it. |
| Circus / Haunted House attractions | Use the intended ride, show, or walk-through flow after inspecting the actual asset. | Expose only meaningful machinery, show, lighting, or sound controls. Do not invent an empty operator interface for scenery. |

The known names above are a starting inventory. Audit the runtime world and lighting sublevels for every ride and repeated instance. All placed rides in the playable demo must pass their own acceptance checks.

**Implementation findings and approach**

The native controller already uses Enhanced Input with separate player and motorcycle mapping contexts. The examined setup script configures keyboard/mouse mappings; its contents do not establish full gamepad support. The current native look handler passes values directly to yaw/pitch, vehicle actions lack release/cancel resets, and a combined interact/mount action will need separation or deliberate contextual arbitration. These are implementation tasks, not just button labels.

Extend gameplay mappings with distinct walking, vehicle, ride-passenger, operator, and UI contexts. Unreal's Enhanced Input supports runtime context changes, analog actions, dead zones, and remapping, which fits this design. [Epic: Enhanced Input](https://dev.epicgames.com/documentation/unreal-engine/enhanced-input-in-unreal-engine).

Build controller-driven menu focus and device-appropriate prompts. CommonUI/CommonInput is a candidate for navigation and controller data assets; evaluate its integration with the project's installed engine and package before selecting the final UI path. [Epic: CommonUI Quickstart](https://dev.epicgames.com/documentation/unreal-engine/common-ui-quickstart-guide-for-unreal-engine).

Device input is a separate task from gameplay mappings and button artwork. Evaluate the installed Windows controller backends for DualSense USB/Bluetooth; a compatibility route such as Steam Input may be useful for additional devices but must be documented and tested if used. Steam Input documents support for multiple controller families. [Valve: Steam Input Devices](https://partner.steamgames.com/doc/features/steam_controller/device).

**Acceptance checks**

- [ ] DualSense inputs and intended connection modes work in a standalone development package; required support components are included.
- [ ] The entire story and free-play flow can be completed with controller alone, including every menu, clue, pickup, and confirmation.
- [ ] Every ride passes boarding, operation, complete cycle, exit, and repeat-use checks; every applicable operator station works with the controller.
- [ ] Every attraction has visible attendant coverage and completes a real attendant-run cycle with the player as a passenger, including a cycle without other guests.
- [ ] Applicable operator handover and attendant resumption work without duplicate commands, unexpected restarts, stranded passengers, or blocked exits.
- [ ] Staff remain present and functional when returning from the mansion, when crowd density changes, and after restarting or reconnecting a controller.
- [ ] Walking, riding, driving, operator mode, menus, and pause never produce overlapping actions or stuck inputs.
- [ ] Look sensitivity remains consistent across different frame rates; full/partial stick and trigger deflections produce the expected response.
- [ ] Prompts match the active device and the player's remapped controls; settings survive restarting the executable.
- [ ] Disconnection, reconnection, and switching to/from keyboard/mouse preserve progress and restore usable input.
- [ ] Vibration settings work, and a controller without special feedback can still perform all essential actions.
- [ ] The wider supported controller matrix is tested, with device/connection/backend results recorded separately.

Related files: `Docs/FIRST_DEMO_DESIGN.md` and `Docs/PLAYABLE_DEMO_CHECKLIST.md`.
