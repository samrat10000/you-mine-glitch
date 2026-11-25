# YOU ARE MY WORLD: SHOT RULES

Status: **Master `01_hilltop_v3` RENDERED & VERIFIED (2026-11-25) — Extreme Photographic Realism + Stardust Grain Girl + Universe Glitch Delivered for Director Review**.
Legacy versions preserved immutable: `ep1/01_hilltop/v1/` (`bg/`), `ep1/01_hilltop/v2/` (`bg_v2/`). Active `v3` pipeline reuses `v2/cel/` (`build_s01.py`, `rig_mh.py`) paired with `ep1/01_hilltop/src/paint_bg_v3.py` (`bg_v3/`) and `ep1/01_hilltop/src/fx_v3.py` (`v3/`).

## 0. Style Override (`R0` Amendment)
- **Approved by Director (2026-11-25):** Overrides `motion2d/RULEBOOK.md R0` blanket ban on *"dotted/dither looks"* and *"dreamcore"* specifically for this project's **dreamcore luminous silhouette + refined iridescent CRT phosphor halftone** visual language.
- **Unchanged Non-Negotiables:** Real rigged MakeHuman CC0 human anatomy (zero stick figures/primitives), analytic 2-bone IK hand clasp (`<= 2.0 cm`), grounded feet (`0 +- 0.5 cm`), sculpted 3D garments & multi-strand hair, multi-plane sculpted clouds, >= 1400 individual grass blades + bokeh depth, characters on twos, camera/sky/particles on ones, full 1:1 crop QA before full render.

## 1. Layers
1. **Character Normal/Mask Passes (`build_s01.py` / `rig_mh.py`):** Pure-NumPy + PIL 2x SSAA triangle rasterizer with alpha-normalized Gaussian shading smooth (`sig = 2.6 * H / 1920`), `1080x1920`, RGBA PNGs:
   - `girl_NNN.png`: `R` = core glow mask, `G` = soft internal depth (`0.5 + 0.5*(N dot L_soft)`), `B` = Fresnel rim `(1 - |N dot V|)^1.65`, `A` = AA alpha.
   - `boy_NNN.png`: `R` = wrapped radiance `pow(clip(raw_nl*0.72 + 0.34), 1.05) * height_mask`, `G` = girl-facing Fresnel rim, `B` = cool shadow fill volume, `A` = AA alpha.
2. **Painted Multi-Plane BG (`paint_bg01.py`):** `115%` oversize (`1242x2208`) RGBA layers (`sky_base.png`, `cloud_far.png`, `cloud_mid.png`, `cloud_core.png`, `grass_mid.png`, `grass_fg_bokeh.png`), 3-octave bicubic FBM + Beer-Lambert directional optical shadowing + pure-NumPy float32 Gaussian blur (zero `scipy`).
3. **Optical Composite (`comp_s01.py`):** True float32 linear/HDR processing with single-thread BLAS inside 4 worker processes (`OMP/OPENBLAS/MKL_NUM_THREADS=1`).
4. **Encode:**
   - Master: `ffmpeg -y -framerate 24 -i v1/comp/%03d.png -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p 01_hilltop_v1.mp4`
   - IG: `ffmpeg -y -i 01_hilltop_v1.mp4 -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -movflags +faststart 01_hilltop_v1_IG.mp4`

## 2. Characters & Contact Truth
- **Girl:** CC0 MakeHuman slender female (`1.62 m`), standing right-of-center (`x = 0.30, y = 0.18`), feet grounded (`Z = 0.0 cm`), closed shoe shell, modest smooth bodice + 24-pleat dynamic A-line mini-skirt + cohesive back-hair veil & 26 wind-animated ribbon strands.
- **Boy:** CC0 MakeHuman lean male (`1.72 m`), seated on rising left knoll (`x = -0.43, y = 0.14, z = -0.73`, `yaw = 120`), relaxed boxy hoodie + tapered cuffs + back fold relief + tousled curls, left hand tucked cleanly behind far knee/grass.
- **Contacts:** Max measured IK error across all 120 unique poses = `1.120 cm` (`<= 2.0 cm`); `girl_foot_z_cm = 0.0` (`0 +- 0.5 cm`).
- **Cadence:** Characters on twos (`fpose = f - ((f - 1) % 2)`); strictly periodic over `240` frames (`phi = 2*pi*(fpose - 1)/240`).

## 3. Look & Lighting
- **Girl Luminous Silhouette:** Incandescent core `#FFFDF8` blended with inner rose-peach `#F6AECC` from `G` channel + white Fresnel rim; Boy's halftone fingers softly layered over palm (`0.74 * exp(-(d_clasp/0.028)^2)`) before halation.
- **Boy Midnight + CRT Halftone:** Shadow `#161448` -> `#272878`. `rad_raw = clip(0.95*R + 0.90*G + 0.14*B, 0, 1.35)` sampled onto a `5 px` rounded-square phosphor dot-matrix (`cell=5`), colored by smooth periodic aurora (`phi + 0.15 - d_clasp * 3.8`: `#2CE0FF` -> `#3558FF` -> `#8D2EFF` -> `#FF24E2`) + gentle 12 fps analog sparkle boil.

## 4. Painted Sky, Clouds & Grass (`paint_bg01.py`)
- **Sky:** `#16104B` -> `#24196C` -> `#2F207E` -> `#351E76` -> `#22124A` + subtle nebula band.
- **Asymmetric Cauliflower Cumulus:** `cloud_far` + `cloud_mid` (`#541B62 -> #C4366E -> #F27098 -> #FFACC8`) + `cloud_core` masked seamlessly through `cloud_mid`'s exact puff fields (`#C93D74 -> #F26C98 -> #FFA4C4 -> #FFCADB`).
- **Grass:** 1400 fine wispy curved blades (`2x SSAA`) along sloping ridge (`y=81.8%` left knoll -> `86.3%` under Girl) + blurred foreground bokeh blades.

## 5. Composite Stack (`comp_s01.py`, locked `v1` numbers)
- **Parallax & Radiance:** Cyclic `cam_dy = 0.0085*sin(phi)`, `cam_zm = 1 + 0.007*(0.5 - 0.5*cos(phi))`; `cloud_mid` boost `1.04 + 0.06*sin(2*phi)`, `cloud_core` boost `1.06 + 0.08*sin(2*phi) + meteor_flash`.
- **Stars & Meteors:** 60 soft stars + 9 hero 4-point diffraction stars (crescendo at `t=0.89`) + Meteor #1 (`0.2-3.8s`) + Meteor #2 (`5.7-8.1s`).
- **Girl 3-stage HDR Halation:** `h1` (`sigma=4`, `div=2`, `0.38`) + `h2` (`sigma=18`, `div=2`, `#F696BE * 0.58`) + `h3` (`sigma=56`, `div=4`, `#E25490 * 0.36`) + 65 periodic stardust embers.
- **CRT & Film Finish:** Reinhard rolloff above `0.92`, `1 px` radial CA, RGB aperture-grille (`1.045 / 0.975`), scanlines (`6.5%` depth, `3 px` pitch), vignette `0.22`, fast 3-tap grain (`* 0.35 * 0.017`), triangular dither.

## 6. Verified Master Stats (`v3`, 240 frames @ 1080x1920)
- **Outputs:** `ep1/01_hilltop/v3/01_hilltop_v3.mp4` (`CRF 14`, `118,291,121` bytes) & `01_hilltop_v3_IG.mp4` (`CRF 18` faststart, `66,344,682` bytes).
- **Luminance (`v3/qa/stats.json`):** `mean = 0.279` (`0.2786`), `p50 = 0.171` (`0.1706`), `p95 = 0.741` (`0.7413`), `sat = 0.551` (`0.5515`).
- **IK & Grounding (reused `v2/cel/meta.json`):** `max gR=0.0`, `max gL=1.748`, `max bR=0.0`, `max bL=1.984`, `max legR=0.0`, `max legL=0.0 cm` (all `<= 2.0 cm`); `max |footZ|=0.0 cm`.
- **Seamless Loop:** `Frame 240 vs 001 MAE = 0.01843`, `max diff = 0.7725`.
- **Checks:** `no black frames: PASS`, `no frozen consecutive frames: 0 frozen PASS`, `ffprobe` (both MP4s): `1080x1920`, `24/1 fps`, `240` frames, `10.000000 s`.
- **Timings:** `paint_bg_v3.py (bg_v3) = 95.77s`; `fx_v3.py (240f) = 822.80s` (~3.43s/frame wall clock across 4 workers).
- *(Historical `v2` & `v1` baselines preserved immutable in `v2/` and `v1/`.)*

## 7. Improvement Log
- `2026-11-25`: Locked `v1` numbers after 3 probe iterations (`probe_v1` -> `probe_v2` -> `probe_v3` -> `v1`).
- `2026-11-25`: `v1` rejected by Director ("totally looks made of AI"). Redesigned rig, garments, CRT phosphor shader, painted clouds, stars, and meadow grass for `v2` (`probe_v4` stop-gate -> `probe_v5` pass -> 240-frame `v2` master delivered).
- `2026-11-25`: Built `v3` (`paint_bg_v3.py` + `fx_v3.py`) for extreme photographic realism, stardust grain Girl (`3,600` surface glitters + `8,170` rising sparkles), bolide meteors, connected oat-panicle grass, and border-clamped universe-glitch scanline bursts (`probe_v6` pass -> 240-frame `v3` master delivered).

## Director Rejection Rules (2026-11-25)
- **Director Verbatim Note (`v1` Rejection):**
  > "Okay the slide, not slide, a lot of things are here right now. It totally looks made of AI right now. And the actions of the girl, the legs of the girl, everything. She is like scratching her head but why? She shouldn't do that. And the figure that is sitting, it also looks AI. You need to work a lot on this"
- **Binding v2 Visual Tests (all 6 must PASS before any 240-frame v2 render):**
  1. **Zero head-scratching / arm-to-head gesture:** `tuck_lift` and `girl_tuck` are permanently deleted. Girl's far arm stays relaxed beside her fluttering skirt hem, with subtle natural torso/head gaze drift toward Boy and sky.
  2. **Natural straight contrapposto Girl legs (2-bone leg IK):** Zero MakeHuman A-pose spread, zero knock-knees, zero bloated duck wedge shoes. Weight-bearing straight right leg + relaxed ~5 deg left knee contrapposto via `solve_leg_ik`, slim ankles, fitted minimal shoe contour tucked softly behind meadow grass tips (`foot_z = 0 +- 0.5 cm`, leg/arm IK `<= 1.5 cm`).
  3. **Asymmetric wind-draped sundress + silky cohesive hair:** Delete the 24-pleat lampshade cone skirt and spiky bird-wing hair tubes. Narrow waist bodice keeping a crisp negative-space gap between right arm and waist; multi-harmonic organic skirt drapery billowing asymmetrically downwind; silky flowing hair veil + soft downward/rightward S-curve locks.
  4. **Cozy 3/4-back Boy seated close beside Girl (`yaw ~ 148 deg`):** NOT kneeling/praying in sideways CG profile. Youthful 1.10x head-to-shoulder proportion, sculpted raised jacket collar & diagonal cloth back-folds, full 56-tuft tousled curly hair, lower hips nestled behind the left meadow knoll, and relaxed low hand clasp gently cradling Girl's lowered fingers right beside her skirt.
  5. **Organic staggered-hexagonal analog CRT phosphor stipples:** Delete the uniform `5x5` square pixel checkerboard. Jittered staggered hexagonal phosphor dots concentrated on lit jacket folds, right shoulder, forearm & curly hair rims while keeping Boy's shadowed left back deep velvet midnight-indigo; subtle 12-fps hand-drawn organic contour boil on characters.
  6. **Painterly dome-normal sculpted clouds, subtle natural stars & atmospheric meadow:** Dramatic deep-indigo sky coves carving 3 distinct coral cumulus masses (zero pink triangle or Perlin blotches); fine pinpoint night stars + max 3 subtle soft hero glints + sleek needle shooting stars (zero 9 identical giant `+` crosshairs); twilight indigo hill + 1800 varied-height wispy grass blades and tall meadow reeds.
