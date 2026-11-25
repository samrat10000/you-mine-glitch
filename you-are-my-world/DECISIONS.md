# DECISIONS: `you-are-my-world`

## 2026-11-25 — Intake & Creative Direction (Director)
- **Original Reel Analyzed:** `@nickjaykdesign` — `https://www.instagram.com/reel/DfTOgmHufWA/?dmpr=MThodjVnZWhjYmUzaw==` (`9.10 s`, `1080x1920`, ~12 fps, "you are my world"). Reference frames stored in `refs/`.
- **Format Choice:** Director chose **Format A (`go with recommendations`)** — `10.0 s` (`240 frames @ 24 fps`), mathematically seamless single-shot loop.
- **Visual Style Choice:** Director verbatim: `"keep the dreamcore CRT phosphor halftone + luminous silhouette aesthetic"`.
  - Decision: Log explicit `R0` style override in `SHOT_RULES.md` permitting refined CRT phosphor halftone + dreamcore night sky, while keeping all `motion2d` structural disciplines (real rigged human anatomy, zero stick figures, analytic IK hand clasp `<= 2 cm`, grounded feet `0 +- 0.5 cm`, real sculpted garments/hair, multi-plane painted clouds, grass density, and full-size crop QA).
- **Execution Environment Choice:** Director verbatim: `"self-contained pipeline runnable right here"`.
  - Decision: Built 100% locally in pure Python (`numpy 2.5.4` + `pillow 13.0.0`, no `scipy`, no Blender) + `ffmpeg 9.1` using a custom pure-NumPy 1D separable Gaussian filter and 2x SSAA MakeHuman triangle-mesh normal/silhouette rasterizer. No HTML/CSS files created (pure Markdown docs per User Rules #6 & #7).
- **Checkpoint Gate:** Deliver `cast_preview.png`, `bg_preview.png`, and 6-frame `1080x1920` probe QA (`contact.jpg` + 1:1 crops + stats) for review before launching the full 240-frame master render.

## 2026-11-25 — v1 Director Rejection & v2 Complete Redesign Decision
- **Director Rejection (`v1`):** Director inspected `v1` and rejected it as looking `"totally made of AI"` — specifically calling out the Girl's unwanted head-scratching arm raise, her legs/silhouette, and the AI-looking seated Boy figure.
- **v2 Redesign Decisions (`probe_v4` Stop-Gate):**
  1. Keep `v1/` and `bg/` strictly immutable; build `v2` assets in `bg_v2/`, `assets/cast_preview_v2.png`, and `probe_v4/`.
  2. Fix anatomy & proportions at the rig level: youthful `1.10x` Boy head proportion; tapered Girl calves; analytic 2-bone `solve_leg_ik` + flat foot leveling to eliminate MakeHuman A-pose knock-knees/duck feet.
  3. Overhaul acting & silhouettes: delete head-scratching `tuck_lift`; switch Girl to narrow-waist bodice + asymmetric downwind sundress + gravity-first silky hair; move Boy close beside Girl in cozy 3/4 back view (`yaw ~ 148 deg`) with sculpted collar, back-folds (`smooth_iters=3`), and 56-tuft curls.
  4. Replace synthetic textures across the stack: staggered jittered hexagonal analog CRT phosphor dots with high-contrast chiaroscuro + 12-fps contour boil; dome-normal sculpted cumulus clouds with deep indigo sky coves; pinpoint natural stars + sleek needle meteors; atmospheric twilight meadow grass + tall reeds.
  5. Enforce strict `probe_v4` stop-gate: stop after 5-frame `1080x1920` probe + 1:1 crops (`couple_mid`, `boy_closeup`, `girl_legs`, `hands_clasp`) for planner verification before launching 240-frame `v2`.

## 2026-11-25 — v3 Extreme Photographic Realism + Sparkling Grain Girl + "Glitch in the Universe" Overhaul
- **Director Mandate (`v3`):** Moving beyond `v2`'s CRT halftone aesthetic (`"still the clouds, the scene, the grass all look too AI and 3D... it should have that extreme realism and that sparkling noise glitters on the girl... sky, falling star all should look damn realistic... like its made of grains, a glitch in the universe"`).
- **Resolved Design Choices (Director Q&A):**
  1. **Girl Grain Cloud:** Dense luminous pearlescent stardust silhouette (`0.70..0.94` base) encrusted with `3,600` coherent twinkling crystal glints + wind-eroded stardust edges shedding `8,170` swirling curl-wind sparkles (`Class 0..3`) upward into the night sky and onto the Boy.
  2. **Glitch in the Universe:** Constant fine 35mm optical grain + radial chromatic fringing + ambient 1–2 px micro-shimmer slices on Girl, plus 3 synchronized high-energy RGB-split & border-clamped razor scanline tear bursts (`frames 56..63, 112..115, 168..174`) aligned to meteor flares (ZERO macroblock copy-paste).
  3. **Photographic Night Sky, Volumetric Clouds & Meadow:** Dust-laned Milky Way diagonal band (`seed 402/405/409`) with ~5,500 multi-temperature stars; `Lp-7` smooth-merged 3D relief heightfield volumetric cumulus light-marched from twilight horizon sun, night dome sky & Girl front point-light; green-cyan/white-gold bolide meteors with trailing fragmentation sparks above the cloud crown; 3-depth-row curved grass blades + connected nodding oat panicles with backlit rose-gold tips and f/1.4 blur.
  4. **Boy Grounded Silhouette:** Deep velvet silhouette (`#070614..#0F0D24`) with 35mm film grain, rose-champagne grazing rim on right curls/shoulder/forearm/clasped hand, cool indigo sky crown highlight, and stray sparkles drifting from Girl.
  5. **File Isolation:** Added `ep1/01_hilltop/src/paint_bg_v3.py` and `fx_v3.py`; rendered into `bg_v3/`, `probe_v6/`, and `v3/` (preserving `v1/`, `v2/`, `bg/`, `bg_v2/`, `rig_mh.py`, `build_s01.py`, `paint_bg01.py`, `comp_s01.py` untouched).



