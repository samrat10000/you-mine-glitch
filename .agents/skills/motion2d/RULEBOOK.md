# RULEBOOK (R0-R12). Every rule has a TEST. A rule without its test passing is a failed shot.

Numbers below are the ones that produced the approved 5 O'CLOCK shots. Use them as defaults; change one
only with a reason logged in `SHOT_RULES.md`.

## R0. The product, and never AI-made
- "The animation is the thing that will stand it out from others. So it shouldn't be degraded." Show
  full-size PNGs and crf 14 clips; a compressed preview is only ever an extra.
- "100 times" more detail than average. Aim to BEAT the art-form reference (Granite Waves hand-drawn anime
  reels: thin dark line, flat cel, one shadow tone, painted soft BG, one accent colour, held poses with small
  precise motion; see reference/5oclock_ep1v3/granite-waves-study.html). Copy the art form, never its
  characters, scenes or story.
- No image/video generators for picture content, no morphing/warping/puppet-stretch.
- Real-world specifics over generic mood: real signage text, real street furniture, real object shapes.
- No glossy symmetric faces, no smooth airbrushed gradients on characters, no dotted/dither looks, no
  "dreamcore" liminal emptiness. Imperfection: grain, slight drift, uneven placement, weathering.
- References first: every character, creature and real prop gets 3-6 photo references in `refs/` before
  modelling (handlebar, crow, Showa loudspeaker horn, roof tiles, koban, randoseru). Human motion is checked
  against real footage (how a person rides, sweeps, holds a phone).
- **Test:** in the contact sheet, name 5 specific real-world details per frame. If you can't, add detail.
  Render next to reference: silhouette, proportions and parts match.

## R1. Story and hook
- One spine (one hero, one place, one clock, one rule, one thing that escalates). Not miscellaneous.
- Visual hook in the first 3 s, with no explanation needed (day outside / night inside the mirror; the
  leaf blows the other way inside).
- The monster/kaiju is held back and revealed late, in pieces, then whole once.
- One hidden rewatch detail per episode (comments will find it).
- Every episode ends on a question that hooks the next (rule 7 torn out, new ink in the hero's handwriting).
- Show the director PICTURES (storyboard strips), never walls of text. Pitches the director rejected are
  never re-pitched.
- **Test:** the storyboard can be understood with the sound off, from the sketches alone.

## R2. Characters: real models, real proportions
- **Never build organic characters/creatures from primitives** (spheres, ovals, cards, cut-out wings).
  Rejected 3x on the crow: "made of ovals", "cut out wings", "hovering feet". Start from a real rigged
  model with a free licence: VRoid CC0 samples (opengameart "vroid-studio-cc0-models"), CC0 GLBs (e.g. the
  Teh_Bucket raven at raw.githubusercontent.com/nrknithin/html-anime/main/models/library/crow/model.glb).
  meshopt GLBs: `npx @gltf-transform/cli copy in.glb out.glb` first. Use the model's own animation clips.
- Humans: perfect anatomy, hands and limbs. Broken or squeezed arms/fingers read instantly as AI.
- Re-dress real models for the cast (see `lib/` and `reference/.../build_cast.py`): age via proportions
  (kids: thighs x0.74 length, spine x0.86, arms x0.86, neck/head compensated to x1.18-1.20 so the head
  reads big), height from evaluated mesh bounds (grandma 1.46 m, kids 1.28-1.32, adults 1.70+), costume
  pieces built against measured body bands (only the torso, |x| < 0.19 m, so T-pose arms don't widen them).
- Age reads by proportion, not by scale: kids 8-10 have a head:body of about 1:5.5, no adult waist, child
  clothes; the elderly get a 20-30 degree spine hunch, bent knees, a shorter stride, grey hair, age clothes,
  a prop; middle-aged men a thicker waist, rounded shoulders, heavier stance. Uniformly shrinking a teen
  model gives a small teenager (fail). Garments at real scale (an undersized hood was a fail).
- Re-dress pieces must look like the real garment: kappogi apron = narrow bib with soft corners flaring to
  a wide skirt panel that hangs straight from the bust (not following the belly), maekake = waist-to-knee
  panel, hachimaki ring visible above the brow, randoseru = beveled box + straps, yellow school cap.
- The hero's look is locked once approved (Sam: lean, narrow shoulders, slightly long hair, big over-ear
  headphones, oversized grey hoodie with uneven strings, red glasses).
- **Test:** turnaround preview of each character next to its references; ages read correctly at a glance.

## R3. Contact, grip, physical truth
- Feet are locked to the surface every frame: measure the lowest toe in world space, offset the body.
  Never float, never sink ("the crawler looked like it was under the ground").
- **Hands really grip** (director note on 04 v3: "nobody ever grabs a handle like that"): fingers wrap
  around, thumb opposes from the other side, palm in contact, wrist roughly in line with the forearm
  (< 15 degrees cocked). Wrist just outboard of and above the object, hand axis across the bar.
  Implementation: IK wrist target, DAMPED_TRACK aim along the grip, LOCKED_TRACK roll so the palm faces the
  object, finger curl per joint.
- If IK can't reach (error > 2 cm), move the body (lean, hip forward) or the part. Never leave a hand
  floating or resting on top.
- Real objects match a photo reference, not a guess. Mamachari comfort bar: one smooth swept-back bar,
  8-10 cm rise from the stem, swept back 20-25 cm, 56-60 cm at the grips, rubber grips ~12 cm in line with
  the bar end + end flange, clamp on the stem.
- Rig gotchas: VRM rigs are in QUATERNION mode; set `rotation_mode='XYZ'` before `rotation_euler`. Knees
  need per-side pole angles or they cross. Store rest quaternions, restore each frame, then apply deltas
  in rest-local axes (`b.matrix_local.to_3x3().inverted() @ axis`).
- **Test:** full-size crop of each hand from side, top and front, and of each foot contact, BEFORE any
  full render. Print IK error per frame; max <= 2 cm.

## R4. Toon look (cel layer)
- EEVEE, transparent film, Standard view transform, 16 TAA samples, PNG RGBA 1080x1920.
- Material: Diffuse BSDF -> Shader to RGB -> RGB to BW -> x0.5 -> ColorRamp CONSTANT -> Emission.
  Lit threshold 0.035, highlight 0.075 (after x0.5). Measure BW values with a debug render first.
- **ColorRamp colours are linear**: convert sRGB design colours with `lin()` or everything renders pale.
- Two tones + an optional third highlight. Shadow tone stays saturated and warm on backlit leaves/cloth,
  never muddy maroon.
- Ink: warm near-black (0.10, 0.06, 0.08), inverted hull with backface culling. Width >= 0.00075 x camera
  distance (a 1.6 mm hull vanished at 4 m; 3 mm reads). Props 0.003-0.008 m by size.
- Rim: Layer Weight Facing > 0.40 (0.60-0.72 on characters/creatures) AND dot(N, sun) > 0.10 -> warm rim
  (1.0, 0.66-0.80, 0.45-0.55). Rim ONLY on edges facing the sun, never on the far/back edge. No rim on flat cards.
- Props: two tones + rust/dirt multiply from object-space noise. Paint shadow (0.27, 0.25, 0.37), lit (0.62, 0.66, 0.60).
- Lights: world ~0.12, cool fill sun 0.35, warm key sun 5.0 low behind the subject.
- **Restraint** (director chose shot 01 v4 over v5): a simple dark silhouette with a warm rim and a bright
  glow under it. No extra sheen bands, no hard underside terminators, no extra drip textures.
- **Test:** mean and p95 luminance within +-10% of the locked shot's frames (`qa_frames.py --ref`); rim
  visible only on the sun side in the crop.

## R5. Painted backgrounds
- numpy painter at 110% frame size (room for push/drift), slight blur for depth (sigma ~2.2).
- Sky gradient stops (sunset): top (0.13,0.12,0.27), .22 (0.30,0.20,0.38), .42 (0.70,0.36,0.42),
  .58 (0.97,0.55,0.36), .70 (1.0,0.76,0.48), .80 (1.0,0.86,0.62). Sun disk + glows (0.05 and 0.22 falloff)
  placed exactly where the Blender sun projects (build prints SUN_SCREEN).
- Clouds: 3 stratus layers of stretched fbm, crisp edges, sun-lit undersides near the sun, thin gold rims.
- Mountains: 3 fbm ridges (never sine waves) with haze; landmark (1964 radio tower + blinking red light).
- Sea/far shore when the setting has one: glitter, horizon haze.
- **Test:** no NaN/black pixels (clip before pow), the sun position matches SUN_SCREEN within 1%.

## R6. World density (the thing that makes it real)
- Ground in the lower third always has real detail: road paint (centre line, lane text 徐行/とまれ),
  manholes, steel joints, cracks (voronoi edges masked by noise; never plate-like), patches, grates,
  fallen leaves (3 colours, real lobed outlines), tyre marks, kerbs, gutters.
- Roofs: tiles in rows AND columns, eave tile edge, ridge end tiles, antennas, water heaters, weathering.
- Clothes/laundry: real cut (sleeves, collar, hems, legs), folds, seams/prints, pegs and hangers.
- Grass/verges: patchy colour, tufts, kerbs, drains, ruts, edge lines. No cactus-like weeds.
- Big flat areas: depth cues (raised edges catching light, converging rows, repeated shrinking objects,
  haze inside materials via camera depth).
- Small organic props (leaves, petals) have real outlines (maple: 7 pointed lobes, serrated edge, stem notch).
- Local truth: Japan keeps left; signs in Japanese (山田商店, 酒・たばこ); bosai musen loudspeakers on
  poles; curve mirrors; vending machines; konbini bags.
- Painted human figures (far away, in mirrors): bezier silhouettes with hood/shoulder slope, a leg gap,
  shoes and a contact shadow, never boxes.
- New detail must not move an approved layout: give new detail its own RNG stream.
- **Test:** count >= 8 distinct real-world props per frame in the contact sheet.

## R7. Light
- Keep the low sun on screen (sx 0.8-0.9) or, when a building hides it, keep its veiling glare in the comp
  (exp(-d/0.09)*0.30 + exp(-d/0.35)*0.14), so the frame never goes flat (p95 ~0.8+).
- Light wrap from the blurred BG on the cel's inner edge x (0.45 x beam + 0.08). Dust motes in the beam.
- Moving light where possible (the mountain shadow creeps across the fields; power-line shadows flick over
  a rider). Use invisible occluders for shadows of off-screen things.
- **Test:** p95 >= 0.78 on sun-facing shots; sun/glare present in every frame of the shot.

## R8. Animation
- Characters on twos (hold each pose 2 frames), holds on threes for weight, smears on fast moves; camera
  and particles on ones.
- Follow-through on every loose thing: hair (wind axis = bone_dir x up), hoodie strings (spline points),
  bags (damped pendulum), leaves, crow feathers. Blinks via EYE_Close shape key.
- Weight: landings pitch the body up ~40 degrees, legs forward, damped settle, fold in ~0.4 s, ruffle.
  Birds hold, then snap the head.
- Never a frozen pose in a "living" shot. Never stop-start motion: drifts and stops are one smooth curve.
- Vehicles carry speed and direction across cuts. Wheel spokes blur at speed.
- **In-betweens are drawings too**: look at every in-between at full size. An IK in-between with the
  elbow jutting sideways, or a local-rotation slerp swinging the arm out, is a fail; solve the pole
  numerically and keep the elbow low with the hand travelling in front of the body.
- Hold long enough to read (3-5 s for most shots), end on a held pose.
- Run cycles: stride length matched to ground speed (no skating).
- Eye glints: tiny white bead placed each frame from head bones (bone-parent offsets broke).
- **Test:** 12-frame contact sheet shows change in every loose element; no foot slides > 1 cm on contact frames.

## R9. Camera
- See `CAMERA_EDIT.md`. Default lens 32-45 mm vertical sensor fit; low angle on subjects against the sky;
  slow push 2.5-3.5% per shot; handheld documentary micro-drift on street coverage.
- Keep the bottom 15% of the frame (IG UI) free of anything important.
- **Test:** every shot has a camera move or a reason in the storyboard to be locked off.

## R10. Composite and grade
- Order: sky -> sun -> far layers -> haze -> cel (with reflection inserts) -> light wrap -> veiling glare
  -> motes -> bloom (threshold 0.74-0.82, sigma 28, x0.28) -> S-curve (0.55) -> grade (x1.04 + (0.035, 0.02,
  0.05)) -> vignette 0.30 -> grain 0.018 (more in shadows).
- BG pushes slower than the cel layer (parallax 1.2% vs 3.5%), small sine drift.
- Mirrors/screens: render the glass as UV emission (16-bit PNG, read with pypng) and map the painted insert
  through it in the comp; ink seat line, edge falloff, faint sheen and dirt. Real reflections (shop windows):
  a holdout glass + a mirror camera reflected across the glass plane, flipped and inserted where cel alpha < 1.
- Key-frame targets: p95 about 0.8-0.95, p99 >= 0.95, p5 about 0.12-0.19 on sunset shots.
- **Test:** `qa_frames.py --ref` deltas within limits; no banding in the sky (16-bit until the end).

## R11. Sound, voice and music
- See `SOUND_VOICE.md`. Never AI-music beds the director rejected (ACE-Step style). Real recorded
  instruments, a piano-led score written around the lines, real SFX, no sudden music cut-outs.
- **Test:** listening tool readings (earshot) quoted, -14 to -15 LUFS integrated, every line audible.

## R11b. Process
- A locked version changes only with the director's OK; experiments are separate files/versions.
- Commit explicit paths only (a `git add` of a shot folder once staged 831 render files).

## R12. Delivery and naming
- Shots `NN_name_vN.mp4` (crf 14, slow, yuv420p, 24 fps). Full cuts `<show>_ep<N>_vN.mp4`.
- Every shot: clip + 4 full-size PNGs + 1 crop + an honest critique (what's great, what's weak, next).
- Files > 20 MB also as a GitHub raw link (phone previews have no download button).
- **Test:** the version number is new; the critique names at least one real weakness.
