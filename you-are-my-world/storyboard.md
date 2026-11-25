# Storyboard: `you-are-my-world` — Episode 1 (`10.0 s`, `240 frames @ 24 fps`, Seamless Loop)

## 01 hilltop (0.0–10.0 s, 240 frames — seamless cyclic single shot)
- **Act:** Complete wordless visual poem (Hook -> Hero Gesture -> Wind Swell -> Star Crescendo -> Seamless Loop Lead-Out)
- **Camera:** `42 mm` vertical fit, height `~1.05 m` facing hilltop crest (`y ~ 86%`), slow cyclic floating breath (`+-0.7%` scale, `0.9%` smooth periodic vertical parallax float over 240 frames, on ones). Girl framed right-of-center (`x ~ 59%`, `y ~ 52%-86%`), Boy seated left-of-center (`x ~ 37%`, `y ~ 62%-90%`), Hero pink cumulus rising behind (`y ~ 25%-88%`).
- **Cyclic Beat Sheet:**
  - **0.0–1.2 s (f1–29) — Opening Tableau & Meteor Entry:** Boy gazes up at girl with clasped right hands; cyan-cobalt phosphor aurora washes across his back & profile. Meteor #1 enters upper-left (`x ~ 16%, y ~ 3%`). Girl's hair and A-line skirt drift gently right.
  - **1.2–3.8 s (f29–91) — Meteor Bolide & Universe Glitch Burst #1 (`v2`/`v3` updated — NO head-scratching arm raise!):** Girl's outer left arm stays relaxed beside her fluttering skirt while her gaze softly tracks the bolide meteor streaking above the cloud crown (`f36–60`) with green-cyan -> white-gold ionization and terminal fragmentation sparks; brief universe-glitch burst (`f56–63`) shimmers across her stardust silhouette as right hands stay clasped.
  - **3.8–5.6 s (f91–134) — Exhale & Second Breeze:** Girl glides left arm cleanly back down beside her hip; wind eases briefly then catches her 22 hair ribbons and pleated skirt into a rising swell; embers peel off her silhouette into the breeze.
  - **5.6–8.2 s (f134–197) — Full Gust & Magenta Aurora Peak:** Strongest cyclic breeze flares her skirt and layered hair waves rightward; warm magenta-violet aurora pulses across the boy's jacket folds & curls; subtle high-altitude Meteor #2 glides across upper sky (`5.8s–8.0s`); girl tilts head tenderly down toward him.
  - **8.2–10.0 s (f197–240) — Star Crescendo & Seamless Return:** Two prominent upper-right 4-point diffraction stars swell in radiant bloom as all wind waves, arm/head poses, cloud layers, embers, and camera breath return smoothly to `phi = 2*pi` matching Frame 1 seamlessly.
- **What moves:** Girl (weight sway, head tilt, left hair-tuck IK arc, 22 hair strands, 16-pleat dress hem, right hand clasp); Boy (chest breathing, tousled hair flutter, subtle head turn, hand grip); 3 cumulus layers (cyclic drift + internal glow pulse); 9 hero 4-point stars + 55 stars; 2 meteors; 60 stardust embers; 450+ midground grass blades + foreground bokeh grass; iridescent halftone wave.
- **Wow detail:** Visible across the whole loop — the girl's real 3D normal-mapped radiance physically lights the boy's sculpted jacket folds, cheekbones, and curls through a living iridescent CRT phosphor matrix while shedding glowing embers into a sculpted pink thunderhead sky, with zero loop seam.
- **Hands/feet contacts to check:**
  1. `hands_clasp`: Boy `wrist.R` + Girl `wrist.R` tenderly clasped at `x ~ 49%, y ~ 73%` (IK err `<= 2.0 cm`, curled fingers).
  2. `girl_outer_arm`: Girl `wrist.L` stays relaxed and natural beside her skirt hem (NEVER raised to head/temple — `v1` hair-tuck was rejected as looking like head-scratching).
  3. `girl_feet`: Lowest foot vertex anchored at `Z = 0 +- 0.5 cm` tucked naturally into backlit grass.
- **Real references needed:** `refs/ref_contact_00_45.jpg`, `refs/ref_contact_48_90.jpg`, `refs/ref_crop_540_blue.jpg`, `refs/ref_crop_680_magenta.jpg`, `refs/ref_strip_characters.jpg`, `refs/ref_strip_sky.jpg`.
- **How it's built:** `rig_mh.py` (CC0 MakeHuman `base.obj` + `default.mhskel` + `default_weights.mhw` + morphs + 2x SSAA rasterizer) -> `paint_bg01.py` (numpy + PIL layered clouds & grass) -> `build_s01.py` (240f animation on twos) -> `comp_s01.py` (float32 optical HDR + CRT phosphor halftone compositor) -> `ffmpeg` CRF 14 master + CRF 18 `_IG.mp4`.
- **Line(s):** None (wordless visual poem, matching original `0%` text).
- **SFX:** Future optional Phase P6 (ambient night wind, subtle grass rustle, soft shimmering chord swell matching `alixe., LucidDream. • you are my world` pacing).
- **Cut in / cut out:** Seamless cyclic loop (`Frame 240 -> Frame 1` continuous match in pose, clouds, embers, camera, and aurora phase).

