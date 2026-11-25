# QA: the self-review loop and the gates

A gate passes only with evidence written to `QA_LOG.md`: a file path you opened and described, or a
number from a script. "Looks fine" is not evidence.

## The loop (run after building ANYTHING)
1. **Probe**: render 4-6 key frames at 40-50% (first, contact/landing, mid-action, last, any wow frame).
2. **Look**: `python scripts/qa_frames.py <frames_dir> --ref <locked_frame.png> --crops crops.json`.
   It writes `qa/contact.jpg`, full-size crops, and `qa/stats.json` (mean, p50, p95, saturation, deltas vs ref).
   Open the contact sheet AND every crop. Describe each in one specific sentence.
3. **Director's eye** (below): write PASS/FAIL + reason per line.
4. **Fix** root causes, re-probe. Minimum 2 passes per shot (3 for first shot / new character / hero shot).
5. **Full render** only when the probe passes. Then a 10-12 frame contact sheet of the full render + crops.
6. **Send** with an honest critique.

## Director's eye (the things this director has actually rejected; check every one, every shot)
1. Anything organic built from primitives? (ovals, cut-out wings, card leaves, star leaves)
2. Feet hovering or sinking? Hands not gripping / resting on top / wrist bent? Arms squeezed or broken?
3. Does every real object match a photo (handlebar, bike, shop, roof, apron, cap, road text)?
4. Characters look like "stick figures" or plain shapes? Clothes look like shapes instead of garments?
5. Flat empty areas: bare asphalt, plain roofs, plain grass, fields with no depth?
6. Flat light: no sun or glare in frame, p95 < 0.78, rim on the wrong (dark) side?
7. Frozen poses / slideshow pans / stop-start motion / missing follow-through on hair, strings, bags?
8. Outline too thin to read at this distance (< 0.00075 x D)?
9. Anything that looks AI-made (glossy, symmetric, generic dreamcore, dotted/dither)?
10. Over-design: extra sheen bands, too many effects (the simpler v4 won)?
11. Big title text over a best shot? (not allowed; a small stamp is fine)
12. Continuity with the previous shot: light direction, time of day, hero costume, speed and direction.
13. Does the shot deliver its planned wow detail and land its dialogue beat at the planned time?

## Numbers that must hold
| check | limit |
|---|---|
| mean / p95 luminance vs locked reference | within +-10% (night/dark shots: state the target in the card) |
| p95 on sun-facing shots | >= 0.78 |
| IK hand error | <= 2 cm every frame |
| foot contact height | 0 +- 0.5 cm on contact frames |
| outline width | >= 0.00075 x camera distance |
| sun screen position vs SUN_SCREEN | within 1% |
| loudness (final) | -14 to -15 LUFS integrated, true peak <= -1 dBTP |

## Gates
- **G0 Intake**: STATE.md + brief.md exist; asset inventory written; path A/B/C chosen.
- **G1 Story**: one spine, a visual 3 s hook, a late reveal, a hidden detail, an ending question. Shown as pictures.
- **G2 Plan**: storyboard with every shot's camera/move/wow/line/cut; dialogue table; cast sheet. Go-ahead logged (or "proceeded on recommendation").
- **G3 Asset**: each character/prop: turnaround preview vs references; proportions/age read right; outline and rim correct.
- **G4 Shot**: the loop above, all Director's eye lines PASS, numbers hold, sent as its own clip.
- **G5 Sound**: voices approved by the director; earshot readings for every cue; lines sit in the music rests; LUFS.
- **G6 Edit**: cuts land on the planned frames; no black gaps; no music cut-outs; grain/grade consistent; final contact sheet.
- **G7 Learn**: SHOT_RULES.md / MISTAKES.md updated with every note and fix from this project.
