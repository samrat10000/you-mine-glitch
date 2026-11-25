# DECISIONS.md : decisions + to-do (5 O'CLOCK)

Read together with WORKING.md. Keep this short: update entries in place, add new decisions at the bottom of their list, and tick off to-dos.

## Decisions
- 2026-11-22: All work lives in `C:\Users\cross\Downloads\xc`. WORKING.md is the log, DECISIONS.md holds decisions + to-do. Sessions switch accounts by handing off through these two files.
- 2026-11-22: Ep1 v2 is 21.0 s at 24 fps, 1080x1920, five shots cut at 0 / 5.0 / 8.5 / 12.0 / 16.5 / 21.0 s (001 mirror, 002 speaker, 003 sam, 004 street, 005 answer).
- 2026-11-22: Shot 003 is toon 3D Sam (Blender), animated on twos and composited over the drawn lane. The reach has one clean IK in-between (elbow down), the hood is at full size, and the end is held to 3.5 s.
- 2026-11-22: 005 timing is NOTE_T=1.9, BLACK_T=2.6.
- 2026-11-22: Animation quality is what makes the reel stand out, so Sam reviews full-res PNG frames and full-quality clips, never compressed previews.
- 2026-11-22: Teaser jobs have priority on the PC. Run everything else at below-normal priority.
- 2026-11-23: Sam's verdict on Ep1 v2: not up to the mark. It doesn't make him stand out. The look needs rethinking before more polish or sound work.
- 2026-11-22: Sound target is mix_v2.py with the first file per prefix (N1_takeA.mp3 ...), then loudnorm I=-15 LUFS, TP=-1.5.

- 2026-11-23: Sam: make ONE shot perfect, then turn how it was made into rules that every later shot must meet ("we need to make one short perfect, and rest is easy"). The rules live in `ep1v3\SHOT_RULES.md`, locked from 01_speaker_v4. Every Sam note gets added there as a dated rule.

- 2026-11-23: Sam: v4 is the rule now. Build every other shot to it. Whenever Sam gives an improvement note on any shot, add it to ep1v3/SHOT_RULES.md section 10 as a dated rule and apply it to every upcoming shot, not just that one.

- 2026-11-23 (Sam, shot workflow): when a shot is finished, notify Sam right away (message + notification) with the clip and frames. If he doesn't approve or comment within 1 minute, move straight on to the next shot. If he later asks for an improvement on a shot, finish the shot in progress first, then go back and improve the earlier one (and add his note to SHOT_RULES.md for all upcoming shots).

- 2026-11-23 (Sam): every improvement and every decision gets written down: shot craft in `ep1v3/SHOT_RULES.md`, workflow and choices here. At the end, all of it becomes a reusable SKILL (pipeline, rules, self-checks, scripts) so any AI (Claude in VS Code, Claude Code, Codex, anywhere) can make these reels to the same standard.

## To-do (in order)
- [ ] Sam: get the Flow piano takes into `ep1v2\audio\`.
- [ ] Pick the Flow take whose piano starts within the first second and has the clearest rests.
- [ ] In `ep1v2\build\`: `python mix_v2.py <flow take> ..\audio mix_v2.wav`, then loudnorm I=-15 TP=-1.5. Report any WARNING lines.
- [ ] Mux the per-shot clips with sound (001_mirror_v2.mp4 ... 005_answer_v2.mp4) and ep1_v2_full.mp4. Sam reviews shot by shot, then the full cut.
- [ ] Sam: review 003 (reach in-between at f31, hood) on the review page https://claude.ai/artifact/V94KbrwHsd8HBm3CVEuv1i, or on GitHub at `anime-5oclock/ep1v2/review/`.

## Added 2026-11-23 (Claude, VS Code)
Decisions
- 2026-11-23 (Sam): DECISIONS.md is the decision file from now on; every decision goes here. (Supersedes "update entries in place" above: append only, never delete older entries.)
- 2026-11-23 (Sam): Ep1 v2 animation quality is NOT up to the mark. The target is the animation in the reels Sam linked (LINKS.md "Links Sam shared": Granite Waves DeZlMh5M1jI for the 2D look, pseudohuasca DeS2sH9MjFX for the suspense idea). Same craft level; our own characters, scenes and story. Consequence: "picture is done" no longer holds, and the sound mix waits until picture is approved.

Open questions for Sam
- Music: the sound plan's "Flow piano take" is a text-prompted AI generation (Flow Music), which conflicts with the no-AI-music rule. Options: A original score on real recorded piano samples (Claude's pick), B Sam plays/licenses real piano, C keep Flow as an exception. Not decided.
- Voice: the N1-S2 takes are ElevenLabs; WORKING.md section 3 says use a real voice. Not decided.
- Look route for the remake (see to-do). Not decided.

Why v2 misses (our stills vs saved stills frames/f1, f2, f6; the reels were NOT watched in motion this session, no Chrome access)
- 003: reads as a VRoid game model. Sleeve mesh breaks up at the raised elbow (f041), reaching hand is flat with splayed fingers (f031), hoodie is one grey block with no drawn folds, hood not visible, doll-like face, orange light blown out on face.
- 004/005: people are small straight-backed geometric figures, seen from behind or frontal, in near-fixed poses in the sampled frames.
- 002: crows are angular cut-outs. 001/005: vector-clean uniform lines and perfect perspective, no hand-drawn line weight.
- Overall: 4 of 5 shots have no close-up of a person. References in the stills are waist-up/close characters, long angled necks, heavy-lidded expressions, deliberate hands, overlapping foreground figures, muted palette with one accent.
- 5 shots use 3 different rendering styles, so Sam in 003 does not match Sam in 005.

To-do (current order, replaces the order of the list above)
- [ ] Sam: give Claude Chrome access so the linked reels can be watched in motion (Sam signs in to Instagram; Claude never signs in).
- [ ] Sam: pick the look route for shot 003.
- [ ] Remake ONLY 003 as a new version (003_sam_v3.mp4, v2 kept) and show it alone.
- [ ] After 003 is approved: lock Sam's design, remake 005, 004, 002, 001 one at a time.
- [ ] Then music/voice decision, mix, per-shot clips with sound, full cut.

## 2026-11-23 (later): reel watched in Chrome
- Chrome works now (Sam signed in to Instagram himself; Claude never signs in). Do NOT run scripts that seek/step the video: that triggered an Instagram reCAPTCHA once. Normal playback + screenshots only.
- Granite Waves "Mentor Zima" (DeZlMh5M1jI) watched in motion. What it does, which our v2 does not:
  1. Cuts between different CAMERA ideas every 2-3 s: waist-up profile, empty ground/asphalt cutaway (no character), feet-and-footwear close-up (sandal beside a boot), then a straight-on waist-up of a second character. We use 5 wide locked shots.
  2. Characters are drawn with long necks, angled heads, heavy lids, wavy hair strands, a necklace pendant and one clear prop, with subtle acting (eyes closed, hand to face).
  3. Foreground figure cropped at the frame edge (dark coat) overlapping the subject: depth from layering.
  4. Muted green-grey painted backgrounds, one maroon/red accent, subtitle in lower third on every line.
- Decision (Claude's proposal, awaiting Sam): remake Ep1 as 5-7 SHORTER, closer shots in that grammar before animating anything (e.g. mirror, speaker, Sam's feet stopping, cup/headphone close-up, Sam profile, street empty, answer). New storyboard first, shown to Sam as stills.
- 2026-11-23 (Sam): Work ONLY inside `xc\anime-5oclock\`. Other folders in xc (dead-roads, teaser, SHARED_ASSETS, _wt_ep1v2, etc.) are not part of this job; do not read, use or touch them. (Exception to resolve: README_PC.md / EP1_V2_SOUND_PLAN.md exist only inside `_wt_ep1v2`; the copy of README_PC.md in `ep1v2\build\` is enough.)
- 2026-11-23: New Ep1 v3 work goes in `anime-5oclock\ep1v3\` (first file: storyboard_v3.png).

## 2026-11-23: corrections to Claude's own entries above + Sam's new note
- Sam: final animation detail must match the linked reels (reel 1 Granite Waves and reel 2 night road) or be better. storyboard_v3.png is block shapes only and shows none of that detail, so it is NOT a style reference and NOT approved.
- Correction: "watched in motion" was about 8 screenshots of reel 1, some behind a pop-up. Cut length "every 2-3 s", hold lengths and hand speed were NOT measured. Reel 2 has not been opened in this session.
- Correction: the reCAPTCHA came while the frame-stepping script was running; that it caused it is likely, not proven.
- Correction: storyboard_v3 dropped text from two lines (N1 "It has never missed one." and P1 "This is Kiriyama Town."), and its shot times were never checked against the voice takes.
- Correction: the second pair of shoes (shot 3) and dark coat figure (shot 5) are Claude's inventions, not in Sam's story, and echo reel 1 shots. Out unless Sam asks for them.
- Correction: the PROFILE and FEET shots are new; the STREET wide stays (shot 6).

## 2026-11-23: 003 v3 made as hand-drawn 2D (Sam said "Go ahead. And make me the reel.")
- Decision (Claude): Sam is now drawn in code in 2D (tapered ink line, flat fill, one shadow tone), no 3D model, because the 3D model read as a game character. Awaiting Sam's yes on the look before shots 001/002/004/005 are remade; shots are shown one by one (Sam's rule).
- Background: existing lane drawing, blurred, desaturated dusk. Red glasses = the one accent.
- Reel 2 watched (3 screenshots): night road, black spiky lattice form grows from a small thing to frame-filling with a matching shadow on the asphalt. Idea for 005 only as suspense method (small wrongness that grows), not its form.
- To-do: [ ] Sam judges 003_sam_v3 [ ] 005 with the same drawn Sam in the mirror [ ] 004 people redrawn [ ] 002 crows redrawn [ ] 001 regrade [ ] storyboard v4 from real frames with full lines [ ] music/voice decision, mix, full cut.
- [ ] Rethink the Ep1 look with Sam (what fell short, which reference to match) before more render/sound work.
- [ ] LATER (Sam will say when): build a reusable skill from the assets in Sam's "hinterland" project and push it to his GitHub repo, so any project on his account can use it.
- [ ] END (spec in SKILL_SPEC.md, following the template Sam gave the teaser thread): turn SHOT_RULES.md + DECISIONS.md + the proven scripts (toonlib, paint_bg, comp, run_full.ps1, the cast/VRM setup, the PC render notes) into one skill (SKILL.md + scripts/ + references/), push it to Sam's repo, and test it from a fresh session.
