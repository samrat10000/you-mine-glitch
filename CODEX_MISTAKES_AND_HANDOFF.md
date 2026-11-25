# CODEX HANDOFF & COMPLETE MISTAKES POST-MORTEM (`you-are-my-world`)

This document is the unfiltered engineering post-mortem and handoff guide for **Codex** taking over `you-are-my-world` (`ep1/01_hilltop`) to push `v4+` to true next-level realism and magic **without repeating a single mistake from `v1`, `v2`, or `v3`**.

---

## 1. Project Goal & Director's Core Vision

- **Reference Inspiration:** Instagram Reel `@nickjaykdesign` (`https://www.instagram.com/reel/DfTOgmHufWA/`, reference stills in `you-are-my-world/refs/`).
- **Format:** `1080x1920` (9:16 vertical), `24 fps`, `10.0 s` (`240 frames`), **mathematically seamless cyclic loop** (`Frame 240 -> Frame 1` zero jump).
- **Director's Current Aesthetic Mandate (supersedes `v1`/`v2` CRT halftone):**
  - **Extreme photographic night-sky & nature realism:** Real astrophotography Milky Way with dust lanes and multi-temperature stars, real bolide shooting star with ionized green-white wake, truly volumetric twilight cumulus clouds lit from within, and photographic backlit meadow grass with shallow depth-of-field blur.
  - **Magical Sparkling Grain-Cloud Girl ("a glitch in the universe"):** She is made of luminous cosmic grains and sparkling noise glitters — dense enough to read as a graceful human figure holding the Boy's hand, while her edges fracture into thousands of twinkling stardust sparkles drifting into the night wind, with subtle dimensional reality-glitch shimmers and 2–3 timed RGB/scanline glitch bursts synchronized with the shooting star.
  - **Grounded Realistic Boy:** Seated close beside her on the grassy ridge in 3/4 back profile, dark grounded silhouette with realistic rim lighting, 35mm film grain, and stray sparkles drifting off the Girl onto him.
- **Skill Rules Installed in Repo:** Read `.agents/skills/motion2d/SKILL.md`, `RULEBOOK.md`, `QA.md`, and `MISTAKES.md` before writing code.
- **Strict Codebase Constraints:**
  - Pure self-contained local Python (`numpy`, `pillow`, `ffmpeg` CLI — note `scipy` is NOT installed unless explicitly added/permitted; `rig_mh.py` has a fast float32 separable 1D `gauss_blur_f32`).
  - Zero CSS and zero HTML tags anywhere in docs/artifacts.
  - Never overwrite legacy version folders (`v1/`, `v2/`, `v3/`, `bg/`, `bg_v2/`, `bg_v3/`) — write new renders into `v4/` / `bg_v4/` / `probe_v7/`.

---

## 2. Quickstart: Rebuilding Regenerable Caches & Running Probes

Raw per-frame PNG caches (`**/comp/`, `**/cel/*.png`, `probe_*/`) and CRF-14 master MP4s (`>100 MiB`) are `.gitignore`d. All `*_IG.mp4` deliveries, key full-res PNG stills, 1:1 crops, `contact.jpg`, `stats.json`, `v2/cel/meta.json`, `bg_v3/*.png`, and MakeHuman CC0 meshes (`you-are-my-world/assets/mh/`) are tracked in Git.

To regenerate the 240 character passes (`v2/cel/*.png`, ~113s on 6 workers) and run a fast 6-frame `1080x1920` gate probe (~30s):

```powershell
# 1. Regenerate 240 character normal/silhouette RGBA passes (120 unique twos-poses)
python you-are-my-world/ep1/01_hilltop/src/build_s01.py you-are-my-world/ep1/01_hilltop/v2/cel 1.0 all

# 2. (Optional) Rebuild v3 background plates (~95s -> ep1/01_hilltop/bg_v3/)
python you-are-my-world/ep1/01_hilltop/src/paint_bg_v3.py

# 3. Run a 6-frame full-res 1080x1920 probe (~30s) BEFORE any 240-frame render
python you-are-my-world/ep1/01_hilltop/src/fx_v3.py you-are-my-world/ep1/01_hilltop/v2/cel you-are-my-world/ep1/01_hilltop/bg_v3 you-are-my-world/ep1/01_hilltop/probe_v7/comp 1,55,59,113,170,240

# 4. Run numeric & contact-sheet QA (ALWAYS open and inspect the images & 1:1 crops!)
python .agents/skills/motion2d/scripts/qa_frames.py you-are-my-world/ep1/01_hilltop/probe_v7/comp --n 6 --out you-are-my-world/ep1/01_hilltop/probe_v7/qa
```

### Channel Encoding of `build_s01.py` Character Passes (`girl_NNN.png`, `boy_NNN.png`)
- **`girl_NNN.png`:** `R` = core mask (`1.0`), `G` = internal soft normal depth (`0.5 + 0.5*(N dot L_soft)`, p5..p95 `0.49..0.96`), `B` = grazing Fresnel rim (`(1 - |N dot V|)^1.65`, p5..p95 `0.00..0.51`), `A` = 2x SSAA silhouette alpha.
- **`boy_NNN.png`:** `R` = Chiaroscuro wrapped radiance facing Girl (`p95 ~ 0.51`), `G` = grazing Fresnel rim facing Girl (`p95 ~ 0.16`), `B` = sky/form volume (`0.57..0.97`), `A` = 2x SSAA silhouette alpha.

---

## 3. Every Mistake Made Across `v1`, `v2`, and `v3` (DO NOT REPEAT THESE)

### Phase `v1` Mistakes (Rejected by Director: *"totally looks made of AI... scratching her head... legs... sitting figure looks AI"*)

1. **MISTAKE 1 — Inventing a "Hair-Tuck" Arm Gesture (`tuck_lift` in `v1` `rig_mh.py`):**
   - **What went wrong:** Animated the Girl's left hand rising to her temple (`f=29..91`) to "tuck windblown hair." In a glowing silhouette without detailed fingers or facial features, an arm repeatedly rising to the side of the skull reads 100% as **scratching her head**.
   - **Hard Rule:** NEVER animate hands rising to the head/face in silhouette. Keep her left (downwind) arm relaxed and graceful beside her fluttering dress hem.

2. **MISTAKE 2 — MakeHuman Rest-Pose Leg Splay Trap (`default.mhskel` FK rotation):**
   - **What went wrong:** MakeHuman's `base.obj` rest skeleton is an A-pose where `upperleg01` slopes `+4.7 cm` outward (`x: 0.108 -> 0.155`) and `lowerleg01` slopes another `+6.2 cm` outward (`x: 0.155 -> 0.217`, ankles `43.4 cm` apart). Rotating `upperleg01` Z by `+-10 deg` via FK bowed the knees inward (`)(` knock-knees) and rolled the ankles into splayed "duck feet."
   - **Hard Rule:** Always drive Girl's legs through analytic 2-bone `solve_leg_ik` + world-flat foot leveling (`err_leg_R = 0.0`, `err_leg_L = 0.0 cm`, `girl_foot_z = 0.0 cm`).

3. **MISTAKE 3 — Bare MakeHuman Toes Poking Through Offset Shoe Shells:**
   - **What went wrong:** Inflating foot vertices along normals to fake shoes left individual skeletal toes (`z < 0.088 m`) protruding through the shell.
   - **Hard Rule:** Filter bare foot triangles below `z < 0.088 m` from `T_body` and use closed lofted shoe shells (`girl_shoe_L`, `girl_shoe_R`) tucked behind foreground grass blades.

4. **MISTAKE 4 — Rigid 24-Pleat Cone Skirt & Spiky "Bird-Wing" Hair Tubes:**
   - **What went wrong:** Uniform `cos(24 * theta)` pleats created a stiff lampshade traffic cone, and straight parametric hair tubes flared outward like stiff angel wings.
   - **Hard Rule:** Use multi-harmonic asymmetric downwind cloth waves and gravity-first crown-tangent hair veils.

5. **MISTAKE 5 — AI-Looking Kneeling Boy Proportions, Helmet Hair Flap & "Broccoli" Curls (`v1` & `probe_v4`):**
   - **What went wrong:**
     - Default MakeHuman `1.0x` male head looks tiny/clinical -> needed `1.10x` youthful head scale above `z = 1.40`.
     - Sideways `yaw = 120` upright kneeling pose looked stiff and artificial -> moved to cozy 3/4-back view (`b_root_pos=(-0.28, 0.03, -0.60)`, `yaw = 152`) with pelvis/knees tucked below the grassy ridge.
     - Placing curls on an analytic sphere (`hy = -0.120`) failed because the scaled cranium occiput extends back to `y = +0.046` (`0.166 m` radius), burying back curls inside `boy_hair_cap` (`+0.068`), leaving a boxy nape "helmet flap" on the left and lumpy Fibonacci "broccoli" balls on his right cheek!
   - **Hard Rule:** Sample hair curls/strands directly on evaluated `boy_hair_cap` surface vertices + surface normals (`N_cap`) with tapered nape sizing.

6. **MISTAKE 6 — `5x5` Square Lego Checkerboard, Pink Triangle Cloud, Giant `+` Stars & Lollipop Grass (`v1`):**
   - **What went wrong:** Axis-aligned `5 px` square halftone cells, a single triangular Perlin cloud, 9 identical mathematical `+` crosshairs, and black oval reed tips all screamed cheap procedural CG/AI.

---

### Phase `v2` Mistakes (Rejected by Director: *"clouds, scene, grass still look too AI and 3D; missing sparkling noise glitters on the girl, realistic sky/falling star, made of grains, glitch in the universe"*)

7. **MISTAKE 7 — Smooth 2D Ellipse-Normal "Plastic/3D Clay" Clouds (`v2` `paint_bg01.py`):**
   - **What went wrong:** Computing analytic dome normals `(nx, ny, nz)` from smooth 2D ellipses made the clouds look like airbrushed 3D metaballs/plastic toys rather than real turbulent vapor, paired with an artificial electric-purple cartoon sky.

8. **MISTAKE 8 — Blowing Out the Girl to a Flat `[1.0, 1.0, 1.0]` White Cutout (`v2` `comp_s01.py`):**
   - **What went wrong:** Shading the Girl at `#FFF8F2` + heavy bloom clipped her entire silhouette to pure white `1.0`. That completely erased any internal sparkling grain/glitter texture, merged her hanging right-screen arm into her waist, and washed out the hand-clasp (`01_hilltop_v2_crop_clasp.png`) so her hand vanished into white glare.

9. **MISTAKE 9 — Halation Floor Spill & Negative Reinhard `RuntimeWarning` (`probe_v4` / `v2`):**
   - **What went wrong:** Unmasked Gaussian bloom spilled a milky pink band across the dark earth below her shoes; and running `img / (1 + img)` before `np.maximum(img, 0.0)` caused divide-by-zero warnings on negative FBM excursions.

---

### Phase `v3` Intermediate Traps Caught During `bg_v3` & `probe_v6` (CRITICAL MATH TRAPS)

10. **MISTAKE 10 — 2D Slab Raymarching Turned the Cloud Center into a Dead Black Hole + "Skull Eye-Holes" (`paint_bg_v3.py` draft 1):**
    - **What went wrong:**
      1. Marching 320 px in 2D `(x, y)` through scalar cloud density `D(x, y)` accumulated optical depth `tau ~ 12.8`, extinguishing light in the thick cloud center (`exp(-tau) -> 0`) and creating an ugly dark muddy bruise in the middle of the cloud with only a bright perimeter ring!
      2. Marching the Girl's point-light in 2D *inside* the cloud sheet self-occluded her radiance after 40 px instead of placing her at `+Z` **in front** of the cloud.
      3. Gaps between lower `LOBES_MID` blobs at `(0.40, 0.68)` and `(0.63, 0.62)` punched two dark sky holes right above the ridge that looked like **creepy skull eye-sockets** (pareidolia)!
    - **Hard Rule:** Cloud bases behind the ridge must be bridged solidly (zero enclosed horizon holes), and volumetric cloud lighting must account for 3D camera-facing relief (`+Z`) with the Girl's light source positioned in `+Z` in front of the cloud face.

11. **MISTAKE 11 — `np.maximum` Voronoi Crease Lines, Naive `logsumexp` Sky Floor Lift, & `1 - abs(fbm)` V-Notches (`paint_bg_v3.py` draft 2):**
    - **What went wrong:**
      1. Combining Gaussian cloud lobes with `S = np.maximum(S, g_i)` created sharp Voronoi bisector valleys where `np.gradient(Zh)` produced straight geometric dark lines (`\/`, `|-`) across the cloud domes!
      2. Naive `logsumexp` over `N=20` lobes lifts empty sky (`g_i = 0`) to `ln(20)/k > 0`!
      3. Using `1.0 - np.abs(fbm)` for billow shapes created sharp V-crease derivative jumps wherever `fbm == 0`.
    - **Hard Rule:** Blend metaball lobes with an **`Lp` norm** `(sum g_i^p)^(1/p)` (`p ~ 7`, C-infinity smooth AND strictly `0` in empty sky!) and use smooth soft-abs `1.0 - sqrt(n^2 + eps)` before taking surface gradients.

12. **MISTAKE 12 — Milky Way `rng.random**10` Sandpaper Static & `ridged` Cirrus Confetti (`paint_bg_v3.py` draft 1):**
    - **What went wrong:** Unresolved star noise via `rng.random((H, W)) ** 10` looked like harsh digital white-noise sandpaper, and high-threshold `ridged` FBM cirrus created tiny white lint flecks across the upper sky that looked like sensor dirt.

13. **MISTAKE 13 — Detached Floating Grass Seed-Head "Bugs" (`paint_bg_v3.py` draft 1):**
    - **What went wrong:** Tapering tall grass culm stems to `0.15 px` at `2x` SSAA (`0.075 px` after Lanczos 2x downsample) caused the upper stem to vanish completely while the thicker spikelet polygons at the tip remained opaque — producing black insect-like specks floating in empty air above the hill!
    - **Hard Rule:** Enforce `min_hw >= 0.95 * ss` all the way up seed-bearing stems AND draw a continuous central rachis polygon through every panicle (`_seed_head`).

14. **MISTAKE 14 — Meteor Flare Hidden Behind Hero Cloud Crown (`fx_v3.py` draft 1):**
    - **What went wrong:** Ending Meteor 1 at `(0.60, 0.215)` put its terminal flare behind the hero cloud top (`v ~ 0.19`). Always keep meteor trajectories in open sky bays above cloud tops (`v <= 0.17`).

15. **MISTAKE 15 — MPEG Macroblock Glitch & `np.roll` Screen-Border Wrap Artifacts (`fx_v3.py` draft 1):**
    - **What went wrong:**
      1. Random `16x32` / `48x96` rectangular block copy-paste across the sky looked like ugly broken MP4 codec corruption rather than an intentional universe rift.
      2. Using `np.roll(slice, sh, axis=1)` during horizontal scanline tears wrapped bright cloud/skirt pixels from `x = 1079` onto the dark left screen edge `x = 0` as bright red/cyan ticks!
    - **Hard Rule:** Never copy-paste sky macroblocks, and ALWAYS use edge-clamped horizontal indexing (`_shift_x_clamp`) instead of `np.roll` for scanline tears and RGB splits.

16. **MISTAKE 16 — Coarse Film Grain Swamping Glitter & Breaking Loop Seam + `sin(pi)` NaN (`probe_v6` pass 1):**
    - **What went wrong:** Blurring per-frame Gaussian noise at `sigma = 0.75 * 2.6` with `amp = 0.11` raised `MAE(240, 001)` to `0.04077` (`> 0.030`) and made the Girl read like blurry photocopy static instead of sparkling diamond grains. Also `np.sin(np.pi * 1.0) ** 0.55` produced `NaN` in `float32` because `np.float32(np.pi)` makes `sin(pi) < 0` — always wrap `np.maximum(np.sin(...), 0.0)` before fractional powers!

17. **MISTAKE 17 — Soap-Bubble Bokeh Rings on Pitch-Black Foreground Dirt (`probe_v6` pass 1):**
    - **What went wrong:** Bright-rimmed lens bokeh discs placed at `v = 0.85..0.97` over unlit black foreground hill dirt looked pasted-on because no light sources exist in the foreground shadow.

---

## 4. What Is STILL Not Good Enough in `v3` — High-Impact Targets for Codex (`v4`)

Inspect `you-are-my-world/ep1/01_hilltop/v3/01_hilltop_v3_IG.mp4` and the 1:1 crops in `v3/` (`01_hilltop_v3_crop_girl_grains.png`, `01_hilltop_v3_crop_meteor.png`, `01_hilltop_v3_crop_glitch.png`, `01_hilltop_v3_crop_grass.png`) BEFORE planning `v4`. Here are the honest remaining bottlenecks holding `v3` back from jaw-dropping perfection:

1. **Girl's Interior Grain Structure Still Flattens Her Anatomy & Hand Clasp (`01_hilltop_v3_crop_girl_grains.png`):**
   - Her silhouette interior (`lum ~ 0.74 +- 0.22`) is still too uniformly bright/opaque, which softens her hanging right-screen arm separation against her skirt and blurs her fingers into glow at the hand-clasp.
   - **How Codex can 10x this:** Make her truly **made of structured cosmic particle streams** rather than noisy white alpha! Use `g[..., 1]` (3D surface depth) and `g[..., 2]` (Fresnel rim) to concentrate dense bright stardust streams along her **3D contours, dress folds, hair flow lines, and fingers**, leaving semi-translucent cosmic/nebula pockets in recessed interior zones so every fold, strand, arm gap, and interlocked finger reads crisply while visibly composed of shimmering micro-grains! Drive shed particles with **2D curl-noise velocity fields** (`dpsi/dy, -dpsi/dx`) instead of simple sine waves.

2. **Boy's Lit Right Arm/Shoulder Still Looks Like Smooth 3D CG Clay (`01_hilltop_v3_f001.png`):**
   - Look at the Boy's right shoulder and bent forearm (`b[..., 0]`): the Gaussian-smoothed MakeHuman vertex normal pass shades his arm like a smooth airbrushed 3D cylinder, giving away the underlying 3D mesh.
   - **How Codex can 10x this:** Sharpen cloth wrinkle/fold normals in `rig_mh.py` (or perturb the rim normal with anisotropic cloth weave/crease FBM in the compositor) and tighten the grazing rim falloff so light catches **crisp fabric folds, cuff edges, and individual backlit hair curls** instead of a wide airbrushed gradient across his biceps. Also clean up the single protruding curl lock at his lower-left nape (`crop_boy`).

3. **Clouds Still Read Slightly Like Pink FBM Heightfields + Detached Top Puff (`01_hilltop_v3_f001.png`):**
   - Remove or blend the small detached `cloud_far` puff sitting right above the hero cloud peak at `v ~ 0.16..0.20` (`LOBES_FAR[0] = (0.66, 0.30)` in `paint_bg_v3.py`).
   - Push cloud realism further with **multi-scale domain-warped Worley-billow / curl-eroded silhouettes** (crisp sunlit cauliflower silver-linings contrasted against deep dark storm-blue bases and warm horizon bounce) + subtle animated internal vapor evolution across the 240-frame loop instead of purely rigid 2D layer panning.

4. **Grass Motion Is Currently Horizontal Row-Shear (`fx_v3.py` lines 509–515):**
   - `gmid` currently sways via a 1D horizontal pixel shift on a static baked PNG. Rendering `grass_far` / `grass_mid` / `grass_near` as separate RGBA layers with **different parallax speeds and phase-offset wind bend** (plus occasional tiny backlit pollen/firefly specks in the grass tips) will create real 3D meadow depth in motion.

5. **"Glitch in the Universe" Art Direction Polish (`01_hilltop_v3_crop_glitch.png`):**
   - Instead of generic full-width horizontal VHS-style scanline tears across the whole sky, try making the glitch feel like a **localized quantum/dimensional anomaly radiating from the Girl and the meteor** — e.g., chromatic prism dispersion, vertical/diagonal pixel-sort stardust streaks, brief frame-echo ghost silhouettes of the Girl offset by a few pixels, and reality-ripple shockwaves expanding from the meteor flare!

---

## 5. Non-Negotiable QA Checklist Before Delivering `v4`

1. **Always run a 5–6 frame `1080x1920` probe first** and visually inspect native `1:1` crops (`girl_grains`, `hands_clasp`, `boy_arm_hair`, `meteor_sky`, `grass_feet`, `glitch_burst`) before rendering 240 frames.
2. **Numeric gates (`qa_frames.py` + `ffprobe`):**
   - `1080x1920`, `24/1 fps`, `240` frames, `10.000000 s`
   - `0` black frames, `0` frozen consecutive frames
   - `Frame 240 vs 001 MAE <= 0.025` (every periodic wave must use integer multiples of `phi = 2*pi*(f-1)/240`; particle lifetimes must wrap on integer cycles per loop)
   - `IK <= 2.0 cm`, `footZ = 0.0 +- 0.5 cm` if `rig_mh.py` is touched.
