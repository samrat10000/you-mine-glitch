# 5 O'CLOCK: SHOT RULES (from shot 01 v4, the locked quality bar)

Sam locked **01_speaker_v4** on 2026-11-23 ("v4 was more better, keep v4"). Every later shot follows this recipe and must reach at least this level. Exact code: `src/build_s01_v4.py`, `src/paint_bg.py`, `src/comp_s01.py` (v4 state), `src/run_full.sh`.

## 1. Layers
1. **Cel layer:** Blender EEVEE, transparent film, 1080x1920, Standard view transform, 16 TAA samples, PNG RGBA.
2. **Painted BG:** numpy painter at 110% size (for push and drift), slightly blurred for depth of field.
3. **Composite:** BG pushes slower than the cel layer (parallax), then light wrap, bloom, dust motes in the sun beam, grade, vignette and grain.
4. **Encode:** `ffmpeg -framerate 24 -i %03d.png -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p NN_name_vN.mp4`.

## 2. Characters and creatures
- **Never build organic creatures from primitives** (ovals, spheres, cards). Sam rejected that three times: "made of ovals", "cut out wings", "hovering feet". Start from a real, artist-made, rigged model with a free licence (CC0 / CC-BY) and use its own animation clips.
  - The crow is Teh_Bucket "Raven" (CC0), downloaded from raw.githubusercontent.com/nrknithin/html-anime/main/models/library/crow/model.glb. opengameart.org is blocked from the cloud.
  - It is meshopt-compressed: run `npx @gltf-transform/cli copy` first.
- Prepare the model: smooth shading, Subdivision level 2, toon material, inverted-hull outline at 0.0035 m.
- Real scale first, then frame for drama with the camera.
- **Contact:** feet are locked to the surface every frame. Measure the lowest toe in world space and offset the body so it sits on the surface. Never let a character float.
- **Motion:** blend the model's own clips (e.g. fly, flare, stand) per bone with quaternion slerp. Characters animate **on twos**, the camera on ones.
  - Landings: wings or arms up, body pitched up about 40 degrees, legs forward, then a damped settle, a fold in about 0.4 s and a ruffle.
  - Birds hold, then snap the head.
- Eye glint: a tiny white bead placed each frame from the head and beak bones. Don't use bone-parent offsets; they broke.

## 3. Toon shading (the look)
- Material: Diffuse BSDF > Shader to RGB > RGB to BW > x0.5 > ColorRamp (CONSTANT) > Emission.
- **ColorRamp colours are linear.** Convert sRGB design colours with `lin()`, or everything renders too light.
- Ramp thresholds: lit at 0.035, highlight at 0.075 (after the x0.5). Measure BW values with a debug render before choosing.
- Backlit rim: (Layer Weight Facing > 0.40) AND (dot(normal, sun direction) > -0.15) mixes to a warm rim colour (1.0, 0.66-0.80, 0.45-0.55).
  - Use Facing 0.72 on creatures, so wings don't get stripes.
  - No rim on flat cards.
- World light about 0.12, fill sun 0.35 (cool), key sun 5.0 (warm) behind the subject.
- Ink: warm near-black (0.10, 0.06, 0.08). Inverted hull 0.003-0.008 m by object size, with backface culling.
- Props: two tones plus a rust multiply from object-space noise. Paint shadow tone (0.27, 0.25, 0.37), lit tone (0.62, 0.66, 0.60).

## 4. Painted sky (paint_bg.py)
- Gradient stops:
  - top (0.13, 0.12, 0.27)
  - 0.22 (0.30, 0.20, 0.38)
  - 0.42 (0.70, 0.36, 0.42)
  - 0.58 (0.97, 0.55, 0.36)
  - 0.70 (1.0, 0.76, 0.48)
  - 0.80 (1.0, 0.86, 0.62)
- Sun disk plus two glows (0.05 and 0.22 falloff). Put the sun where the Blender sun projects on screen (the build script prints SUN_SCREEN).
- Three stratus cloud layers from stretched fbm noise: crisp edges, sun-lit undersides near the sun, thin gold rims.
- Mountains: three fbm ridges (not sine waves) with haze, plus the 1964 radio tower with a blinking red light, plus rooftops.

## 5. Composite (comp_s01.py, v4 settings)
- BG blur sigma 2.2. BG push 1.2% over the shot, cel push about 3.5%, small sine drift.
- Light wrap: blurred BG times the cel inner edge, times (0.45 x beam + 0.08).
- Bloom: threshold 0.82, sigma 28, x0.28. Warm beam haze x0.6.
- Dust motes: 70 motes in the sun beam, on twos.
- Grade: x1.04, then + (0.035, 0.02, 0.05).
- Vignette 0.30, grain 0.018, more in the shadows.

## 6. Camera and framing
- Low angle, looking slightly up at the subject against the sky. Lens 38 mm, vertical sensor fit. Subject in the upper-middle third, with the sun low behind it.
- The camera pushes slowly on ones (2.5-3.5% over the shot).

## 7. Speed
- Test at 40-50% resolution on 4-6 key frames. Only render all frames at 100% once the key frames pass.
- Cloud: about 10 s per full-res cel frame on 4 CPUs (EEVEE via software GL) plus about 3 s comp. A 72-frame shot takes about 20 min.

## 8. Self-check before sending (every version)
- Make a contact sheet of 10-12 frames and full-size crops of the face, hands and feet.
- Check against this list:
  - silhouette reads as the real thing
  - no floating or intersecting
  - anatomy right
  - motion has weight and follow-through
  - light matches the sky
  - nothing looks AI-made
  - pixel values checked numerically (previews lie about brightness)
- Send the clip plus 4 full-size PNGs with an honest critique. Never overwrite a version Sam has seen.

## 9. What Sam preferred
- **v4 over v5.** v5 added a profile turn with the crow 35% bigger, a blue sheen band, drip rust, a hard underside terminator, a weaker glow and varied cloud rims. Sam kept v4.
- So keep the v4 restraint: a simpler dark silhouette with a warm rim, a bright glow under the subject, and no extra sheen bands.

## 10. How these rules grow (Sam, 2026-11-23)
These rules are the standard for every shot. Whenever Sam gives a note on any shot, add it here as a new dated rule and apply it to every upcoming shot, not just the one he commented on.

### Improvement log
- 2026-11-23: rules locked from 01_speaker_v4.
- 2026-11-23: 02_mirror_v1 passed (Sam: "this is good, go with this, improve if you can, analyse it"). New rules from its self-check, for every later shot:
  - Small props that are organic (leaves, petals) get a real outline (maple: 7 pointed lobes, serrated edge, stem notch), never a star or simple polygon.
  - Backlit leaves and cloth glow: shadow tone stays saturated and warm, not maroon/dark.
  - Painted human figures (in mirrors, far away) use bezier silhouettes with hood/shoulder slope, a leg gap, shoes and a contact shadow, never box shapes.
  - Mirror/screen inserts: render the glass as UV emission (16-bit PNG, read with pypng), map the painted insert through it in the comp; add an ink seat line, edge falloff, faint sheen and dirt.
  - Keep the sun on screen and low (sx 0.8-0.9) so the bloom and dust beam from the v4 look stay in frame.
  - Flat ground planes need real-world detail (road paint like とまれ, manholes, cracks, kerbs). 02 lacked this; fix it from shot 03 on.
- 2026-11-23 (Sam on 03_kiriyama_v1: "perfect, but..."), for EVERY shot from now on:
  - Clothes and cloth must not look like plain shapes: real garment cut (sleeves, collar/neck hole, hems, legs), folds, seams/prints, pegs and hangers where they hang.
  - Roofs need real detail: tile columns as well as rows, the eave tile edge, ridge end tiles, antennas, water heaters, weathering.
  - Grass, verges and footpaths need texture and props: patchy colour, tufts, kerbs, drains, ruts, edge lines.
  - Big flat areas (fields, plazas, water) need depth cues: raised edges that catch the light, rows that converge, repeated objects that shrink into the distance (racks, sheds, poles), and haze.
- 2026-11-23 (self-check on 04_ride v1-v3), for every shot with characters:
  - Character outlines: at least 0.00075 x camera distance (Sam's 1.6 mm hull vanished at 4 m; 3 mm reads).
  - Backlit characters get the warm rim only on edges facing the sun (normal . sun > 0.10), never on the far/back edge.
  - When a building hides the low sun, keep the sun's veiling glare in the comp so the frame doesn't go flat (aim p95 about 0.8+).
  - Ground in the lower third needs real road paint (centre line, lane text like 徐行, grates, leaves, tyre marks), not bare asphalt.
  - Japan keeps left: cyclists and cars ride on the left side of the road.
- 2026-11-23 (Sam on 04_ride_v3: "nobody grabs a handle like that, a cycle handle is never like that"), for every shot with hands on objects:
  - Handlebars follow the real part: a mamachari comfort bar rises out of the clamp, swings wide, then curves back and down to the grips; rubber grips in line with the bar end, end flange, bar clamp on the stem.
  - Grip = hand wraps the bar: wrist just outboard of and above the rubber, hand axis across the bar (not along it), palm down on top (locked-track roll), fingers curled under, thumb around. Check a close-up render of each hand from the side, top and front before any full render.
  - If the arm can't reach (IK error > 2 cm), move the rider (lean, hip forward) or the part, never leave the hand floating or resting on top.
- 2026-11-23 (same note, wider rules added from the PC: "Look at the cycle handle. Nobody ever grabs a handle like that, and a cycle handle is never like that... Other things, you're going very good."), for EVERY shot from now on:
  - Hands that hold anything (handlebar, broom, phone, door, notebook) must really grip it. The fingers wrap around the object, the thumb opposes from the other side, the palm is in contact, and the wrist stays roughly in line with the forearm. Check a full-size hand crop against a photo reference before rendering all frames.
  - Real-world objects must match a photo reference of the real thing, not a guess. A Japanese mamachari handlebar is one smooth swept-back bar: about 8-10 cm rise from the stem, swept back about 20-25 cm, 56-60 cm wide at the grips, with short rubber grips (about 12 cm) angled slightly outward. It is not two long parallel rods.
