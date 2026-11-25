# STYLES: what changes per style, what never changes

Pick at P0 (`style=`). Default: `toon-anime`.

**Never changes, in any style:** the phases and gates, real models for organic things, contact and grip
truth, real-world density, the low-sun light logic (or the style's equivalent key light), shot-by-shot
delivery, sound last, the rule book growing with every note, honest self-review with crops and numbers.

| style | cel layer | lines | BG | motion | notes |
|---|---|---|---|---|---|
| **toon-anime** (default, 5 O'CLOCK) | EEVEE 2-tone ramp + warm rim | warm near-black inverted hull | numpy painted sky + 3D set | twos, holds on threes | the full recipe in RULEBOOK |
| **3d-ink** (Night Terror look) | 3-tone + texture, stronger shadow | thick black hull + Line Art for creases | 3D set + painted sky | ones for camera, twos for faces | see money-skills/teaser PIPELINE_3D |
| **comic** | 2-tone flat, halftone ONLY in shadows (no full-frame dots: the director dislikes dither) | heavier hull 1.5x, varying by distance | flatter sky, speed lines on fast moves | holds on threes, impact frames | panels = cuts; sound-word SFX only if the user asks |
| **vector-2d** (pycairo drawn) | code-drawn BGs only | stroke width by depth | pycairo + numpy post | twos | characters must still be 3D toon models; drawn people read as stick figures |
| **pixel** | render at 1/4-1/6 res, nearest-up, palette quantise (no dithering) | 1-px dark outline pass | low-res painted | twos/threes | snap camera to whole pixels |
| **sketch-ink** | 1-tone + paper texture | jittered Line Art strokes, boiled every 2 frames | pencil-wash BG | twos | "how it works" reels |

Switching style changes `lib/toonlib.py` parameters (ramp stops, hull width, rim) and `comp` post (halftone,
quantise, paper). Log the chosen parameters as the project's SHOT_RULES section 3.
