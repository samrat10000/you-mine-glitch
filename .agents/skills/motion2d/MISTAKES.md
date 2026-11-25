# MISTAKES: the history behind the rules (5 O'CLOCK, 2026-11-22/23)

| # | what was shown | director's verdict (words) | root cause | fix that worked -> rule |
|---|---|---|---|---|
| 1 | 5 story pitches as text | "I want to picturize it, visualize it" | walls of text | storyboard strips for every pitch -> R1 |
| 2 | all 5 pitches | "None of these interests me... a boy in Japan, strange things, real, rules, only survivor" | generic premises | one spine around a REAL Japanese thing (the 5 PM bosai musen chime) -> R1 |
| 3 | Ep1 v1, pycairo-drawn characters | "totally looks like stickman's" | code-drawn people hit a ceiling | toon-shaded 3D VRoid models over painted BGs -> R2 |
| 4 | Ep1 v2 | "not up to the mark, won't make me stand out" | low detail, slideshow feel | full redo v3: 18 shots, real animation, world density, one perfect shot first -> SKILL contract 2 |
| 5 | music v1-v2 (organ/no piano) | nowhere near the reference | ignored the reference's piano | piano-led score measured from the reference reel -> SOUND_VOICE |
| 6 | (zombie series) AI music beds | "trash" | text-to-music AI | real samples / approved Flow takes -> R11 |
| 7 | shot 01 v1-v3 crow | "made of ovals", "cut out wings", "hovering feet" | primitives for an organic creature | CC0 rigged raven GLB + own clips + toes locked -> R2, R3 |
| 8 | shot 01 v5 (more effects) | "v4 was more better, keep v4" | over-design (sheen band, drip rust, bigger crow) | restraint -> R4 |
| 9 | shot 02 self-check | (caught before sending) star leaf, box figure | lazy prop shapes | maple outline, bezier figure -> R6 |
| 10 | shot 02 | "good... improve if you can" | bare ground plane | road paint/manholes/cracks rule -> R6 |
| 11 | shot 03 v1 | "perfect, but" clothes were shapes, plain roofs, plain grass, no field depth | detail missing | garment builder, kawara rows+columns, tufts/kerbs, levees/racks/poles/haze -> R6 |
| 12 | shot 04 v1 (self) | flat light, plain road, outline vanished | hull 1.6 mm at 4 m; sun hidden | outline >= 0.00075 D, veiling glare, road detail -> R4, R7 |
| 13 | shot 04 v2 (self) | rim on his back | rim not tested against sun direction | rim only where N.sun > 0.10 -> R4 |
| 14 | shot 04 v3 | "Nobody ever grabs a handle like that, and a cycle handle is never like that" | guessed bar shape, hand on top | photo-matched comfort bar + wrap grip with IK/aim/roll + hand crops before full render -> R3 |
| 15 | rider facing backwards (build) | (caught) | VRM rig QUATERNION mode ignored rotation_euler | set rotation_mode XYZ -> R3 gotchas |
| 16 | knees crossed (build) | (caught) | one pole angle for both legs | per-side pole angles (-112 L / -68 R) |
| 17 | EEVEE planar probe reflection (build) | (caught) | probes don't render headless | mirror camera pass + comp insert -> PIPELINE |
| 18 | relative outdir on Windows | (caught) | blender.exe resolved it to C:\test | always absolute outdirs |
| 19 | cast pass 1-3 | (self) teens not grandma/kids; apron warped by T-pose arms; silver hair | VRoid samples are young adults; bands included arms | bone proportions + head compensation, torso-only bands, flat hair colour, straight-hanging apron -> R2 |
| 20 | review PNGs sent as remote file cards | user never saw them | wrong delivery channel | push to git + attach in the thread + raw links -> R12 |
| 21 | whole episode as first look (zombie series) | rejected as a whole, cost days | batch delivery | shot-by-shot delivery -> SKILL contract 5 |
| 22 | Ep1 v2 story, 21 s | "the story line is not that good... needs to be at least 45-65 sec" | too thin to engage | STORY.md skeleton, 45-65 s -> R1 |
| 23 | crow eye glint as a bone-parent offset | two white dots floating a head above the crow | offset in the wrong space | place the glint each frame from bones -> R8 |
| 24 | reach in-between by local slerp, then IK with a bad pole | arm swung out sideways, elbow jutted | unchecked in-betweens | numeric pole, check every in-between -> R8 |
| 25 | undersized hood | hood looked tiny | guessed garment scale | real garment scale from a reference -> R2 |
| 26 | compressed preview as the main file | "it shouldn't be degraded" | delivery | full-size PNGs + crf 14 -> R0 |
| 27 | music judged only by loudness | called it an organ drone; the director heard a piano | no attack/pitch analysis | detect note attacks, say what you can't hear, trust the director's ear -> SOUND_VOICE |
| 28 | changed a locked version without asking (crow v6 experiment) | - | scope creep | locked versions change only with an OK -> R11b |
| 29 | PowerShell Start-Process ExitCode empty | exit check failed | handle not held | `$null = $p.Handle` before WaitForExit (scripts/run_shot.ps1) |
| 30 | cached `ROAD.matrix_world` was stale (copied before a view-layer update) | kids sank 1.2 m under the road, IK errors 20-236 cm | matrix_world is only refreshed by `view_layer.update()` | call `bpy.context.view_layer.update()` before copying any matrix_world; print hip/ankle road-local numbers when IK errors are huge |
| 31 | leaked pose-bone scale (`pb.matrix = ...` assignment and a `reset()` that left scale alone) | arms stretched 20-30% in later frames | shear leaks in when a bone matrix is set under a rotated parent | in reset and after every aim set `pb.scale=(1,1,1)`, then aim once more; log bone lengths before/after |
| 32 | road-local numbers used as world coordinates on a sloped road | camera, broom tip and shutter off by up to 2.3 m | the road empty is rotated 3.5 degrees | one `RW(v)` (points) and `RD(v)` (directions) helper; never mix |
| 33 | IK targets out of reach (hands at 0.8 m with 0.44 m arms) | floating or hyper-extended arms | targets chosen by eye | place the hands relative to the shoulders first, then fit the prop to the hands; gate: IK error under 4 cm on every probe frame |
