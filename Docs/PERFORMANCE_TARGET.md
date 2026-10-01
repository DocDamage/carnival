# Demo performance target

User confirmed September 30, 2026: **30 FPS minimum, 60 FPS target**, using this
PC as the reference machine. Use 1920×1080 as the initial benchmark resolution,
matching the reported RTX display; other resolutions/settings remain to be tested.

- Intel Core i5-14600K, 14 cores / 20 logical processors.
- 47.77 GiB usable physical RAM (approximately 48 GB installed).
- NVIDIA GeForce RTX 3060, **12 GiB VRAM**, driver 596.49.
- Windows 11 Pro, build 26200.
- Project drive F: approximately 134 GiB free at the scan.

Raw hardware evidence: `Saved/PerformanceAcceptance/TargetPC_20260930.json`.
The Win32_VideoController AdapterRAM field overflows for this GPU; the 12 GiB
value is from NVIDIA's installed `nvidia-smi`, not that unreliable WMI field.

Acceptance requires the current fully cooked, populated game at documented
graphics settings, across travel, interiors, rides, vehicles, and extended play.
Record CPU/GPU frame times, 1% lows, hitches, RAM/VRAM, loading and repeat-run
stability. A 30 FPS minimum corresponds to a 33.33 ms frame budget; 60 FPS is
16.67 ms. Editor captures and a hardware scan do not accept this target.
