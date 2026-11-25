# Brief: `you-are-my-world` (100x 2D Dreamcore CRT Recreation)

- **Reference:** Instagram Reel [`DfTOgmHufWA`](https://www.instagram.com/reel/DfTOgmHufWA/?dmpr=MThodjVnZWhjYmUzaw==) by `@nickjaykdesign` ("you are my world", 9.10 s, 16K likes)
- **Goal:** Recreate the Reel in 2D animation **100x better** using `make-motion2d` disciplines (`R0-R12`, `QA.md`, `MISTAKES.md`) in a **100% self-contained pure-Python (`numpy` + `pillow` + `ffmpeg`) pipeline** runnable directly on this machine.
- **Format:** `1080x1920` (9:16), `24 fps`, **`10.0 s` (`240 frames`) mathematically seamless loop**
  - Characters animated on **twos** (120 unique poses, zero frozen statue poses)
  - Camera float, 3-layer clouds, 4-point diffraction stars, 2 staggered shooting stars, stardust embers, grass wind, and aurora halftone wave animated on **ones**
- **Style Override (approved by Director):** Keep the **dreamcore CRT phosphor halftone + luminous silhouette aesthetic** (`SHOT_RULES.md` logs the project override to `R0` default "no dither/dreamcore").
- **100x Upgrade Pillars:**
  1. **True Rigged Anatomy & Secondary Motion:** Real MakeHuman CC0 163-bone rigs with 2-bone analytic IK clasp (`<= 2 cm`), expressive silhouettes, boy breathing + hair flutter + meteor-tracking head turn, girl weight sway + hair-tuck arc + 22-strand wavy wind hair + pleated A-line dress billowing.
  2. **3D Normal-Driven Iridescent Phosphor Halftone:** Real `N dot L` + Fresnel rim from the girl's radiant center mapped onto a crisp `5 px` CRT phosphor dot-matrix flowing cyan -> cobalt -> violet -> neon magenta with gentle 12 fps analog shimmer (no harsh unmotivated RGB strobe).
  3. **Layered Luminous Girl + Embers:** Incandescent ivory core (`#FFFDF7`) with delicate rose-peach subsurface depth (`G` channel) so hair locks & dress pleats stay legible inside a 3-stage HDR float32 halation glow, shedding stardust embers into the night wind.
  4. **Multi-Plane Sculpted Cumulus & Backlit Grass:** 3 depth layers of cauliflower cumulus thunderheads with domain-warped FBM edges, volumetric self-shadowing, and internal radiance breathing; 450+ individual wind-swayed grass blades + foreground bokeh depth.
  5. **Seamless Mathematical Loop:** Every oscillator is strictly periodic over `240` frames (`phi = 2*pi*(f-1)/240`), eliminating the original `9.10s -> 0.00s` jump seam.

