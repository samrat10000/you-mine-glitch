---
name: motion2d
description: Build a 2D anime / toon motion-graphics reel or episode (vertical 9:16, 15-90 s) shot by shot to final quality, from an idea, a poster or existing assets, in any chosen 2D-looking style. Use when the user types /motion2d or asks for a 2D reel, anime short, toon episode or a shot of one.
---

# /motion2d: 2D anime reels that pass the director in one round

Usage: `/motion2d <idea, episode or shot> [style=<style>] [assets=<folder>] [poster=<file>] [length=<s>] [shot=<NN>]`

Examples:
- `/motion2d 5 O'CLOCK episode 2 "The Koban" assets=C:\Users\cross\Downloads\xc\anime-5oclock`
- `/motion2d shot=05 the ritual` (continue an episode: reads its STATE.md and builds that shot)
- `/motion2d a girl finds a vending machine that sells yesterday style=toon-anime length=45`
- `/motion2d poster=listener.png style=comic` (poster becomes the hero frame)

This skill is the distilled method behind the 5 O'CLOCK Ep1 v3 shots (2026-11-23). The director said of
them: "you're doing absolutely crazy... maybe one more iteration, or not even an iteration." The first two
versions of that reel (code-drawn vector characters) were rejected as "stick figures" and "not up to the
mark". Everything that changed between those and v3 is written here as a rule with its test. Your job is
to reach the v3 level on the FIRST version you show, and then go beyond it.

## Non-negotiable operating contract (read first, every time)

1. **Read the whole skill before you act**, in this order: this file, `DISCIPLINE.md`, `STORY.md`, `RULEBOOK.md`,
   `QA.md`, `PIPELINE.md`, `STYLES.md`, `CAMERA_EDIT.md`, `SOUND_VOICE.md`, `ENVIRONMENT.md`.
   `MISTAKES.md` is the history behind the rules (read it once). `PLAYBOOK_5OCLOCK.md` is a full worked
   episode (18 shots, every camera, cut, voice line and technique): copy its level of planning.
   After a context compaction, re-read `RULEBOOK.md`, `QA.md` and the project's `STATE.md` before the
   next action.
2. **One perfect shot first.** The first shot is iterated until the director locks it. Its exact recipe
   (numbers, not adjectives) becomes the project's `SHOT_RULES.md`, and every later shot must match or
   beat it. Never mass-produce shots before the first one is locked.
3. **Every note becomes a rule for every shot.** When the director comments on any shot, write the note
   (verbatim + the general rule + the test) as a dated line in `SHOT_RULES.md` and apply it to ALL later
   shots, not only the one commented on. Also widen it: a note about a bicycle handle is a rule about
   every hand that holds anything and every real object that must match a photo.
4. **You are your own harshest reviewer.** After building anything (a prop, a character pose, a shot),
   look at it: contact sheet + full-size crops of hands, faces, feet and the wow detail + pixel numbers
   (`scripts/qa_frames.py`). Then run the Director's eye list in `QA.md`. Fix, re-check. Minimum 2
   review passes per shot, 3 for the first shot, any new character, and the hero shot.
5. **Shot by shot delivery.** Each shot goes to the director as its own clip (`NN_name_vN.mp4`) +
   4 full-size PNGs + one hand/face crop + an honest critique the moment it is done. If there is no
   reply within ~1 minute, start the next shot. If notes arrive later, finish the current shot first,
   then fix the earlier one. Never send a whole episode as the first look. Never overwrite a version the
   director has seen (v1, v2, ... forever).
6. **Sound last.** Voices, score and SFX are made only after the pictures are approved, then mixed
   around the lines (see `SOUND_VOICE.md`). The animation timing is still planned against the dialogue
   table from day one.
7. **Keep state on disk** in the project folder: `STATE.md` (phase, shot statuses, next step, paths),
   `SHOT_RULES.md`, `DECISIONS.md` (director's words verbatim + decision), `MISTAKES.md` (what was
   rejected + the fix), `WORKING.md` (what was done), `QA_LOG.md`. Any model or AI must be able to resume
   from these alone.
8. **Never** enter passwords or change system settings (power, drivers); ask the user. Never post online.
   Never claim "done", "fixed", "synced" without a file or a number that proves it.

## Inputs: decide the path in Phase 0

| What you got | Path |
|---|---|
| Characters + sets exist (blends, VRMs, previous episode) | **A**: inventory, reuse the cast and the locked look, build only what is missing. |
| A poster only | **B**: the poster is the hero frame; build cast + world to match it first (turnarounds checked against the poster). |
| An idea only | **C**: story first (5 pitches as PICTURE strips, not text), then cast, then the first perfect shot. |
| A previous episode in this skill's format | **A+**: read its `SHOT_RULES.md` + `PLAYBOOK`; the bar is that episode's best shot. |

## Phases (gates in QA.md; never skip one)

- **P0 Intake.** Parse idea/style/length. Defaults: 1080x1920, 24 fps, characters on twos, camera on ones,
  no on-screen title text over shots (a small stamp like `KIRIYAMA · DAY 001 · 17:00` is allowed).
  Inventory assets (file, what it shows, quality 1-5, already approved?). Write `STATE.md`, `brief.md`.
  Ask at most ONE batched question, only if the hero or style is ambiguous.
- **P1 Story.** One spine: one hero, one place, one clock, one rule, one thing that grows. A hook in the
  first 3 s that is visual (day outside / night inside the mirror). Research real-world specifics of the
  setting (they are what makes it not look AI). Show the director pictures (storyboard strips), keep text short.
- **P2 Plan.** A storyboard artifact/page: per shot number_name, time range, camera (lens, height, move),
  what moves, the wow detail, the dialogue line(s) that land in it, the cut into the next shot. Plus the
  full dialogue table (time, shot, who, line, delivery) and the cast sheet. Template:
  `templates/storyboard_shot.md`; worked example: `PLAYBOOK_5OCLOCK.md`. Get one go-ahead; if the director is
  away, proceed on your recommendation and say so.
- **P3 Cast + world assets.** Real artist-made models (VRoid CC0, CC0 GLBs), never organic primitives.
  Toon-convert, outline, proportion, re-dress, turnaround preview, check against references (G3).
- **P4 First perfect shot.** Build -> 4-6 key frames at 40-50% -> QA -> fix -> full render -> send. Iterate
  until locked. Then write `SHOT_RULES.md` from it (template `templates/SHOT_RULES_template.md`).
- **P5 Remaining shots**, one at a time, in story order (or hardest first if the plan says so), each through
  G4 and delivered on its own.
- **P6 Voice + music + SFX** on the locked picture (G5).
- **P7 Edit + master**: join with the planned cuts, one grade, loudness, encode (G6). Deliver clips, the
  full cut, and direct GitHub download links for big files.
- **P8 Learn.** Append every lesson to `SHOT_RULES.md` / `MISTAKES.md`, and propose updates to this skill.

## The things that made v3 great (never lose these)

1. **Real models, toon-rendered.** Characters and creatures are rigged artist-made models (VRoid/VRM, CC0
   GLB) converted to 2-tone toon + ink hull, animated on twos. Code-drawn people read as stick figures.
2. **One look recipe**: painted numpy sky + EEVEE cel layer + composite (parallax, light wrap, bloom, dust
   in the sun beam, veiling glare, grade, vignette, grain). The low sun is on screen or its glare is.
3. **Real-world density**: road paint and text, manholes, cracks, leaves, tyre marks, kerbs, wires,
   tiles in rows AND columns, garments with real cuts, signs in the local language, left-hand traffic in Japan.
4. **Contact and grip**: feet locked to the ground, hands wrap what they hold, objects match a photo.
5. **Restraint**: one warm rim on sun-facing edges, one red accent colour, no extra sheen bands
   (the director preferred the simpler v4 of shot 01 over the busier v5).
6. **A hidden rewatch detail** per episode (a reflection half a second late), built for real (mirror camera).

## Files

| file | what |
|---|---|
| DISCIPLINE.md | agent behaviour: VS Code extension, Codex, small models, why the desktop run was better |
| STORY.md | story spine, 45-65 s beat skeleton, series devices, dialogue format |
| RULEBOOK.md | every rule with its test (R0-R12) |
| QA.md | self-review loop, Director's eye list, gates G0-G7 |
| PIPELINE.md | exact build/paint/comp/encode recipe, file layout, commands, timings |
| STYLES.md | style switch (toon-anime default, 3d-ink, comic, vector-2d, pixel, sketch) |
| CAMERA_EDIT.md | camera grammar, shot types, cuts, joins, transitions, timing to the beat |
| SOUND_VOICE.md | narrator + character voices, score around lines, real SFX, mix numbers |
| ENVIRONMENT.md | machines (Asus render box), cloud, model routing, token rules, delivery links |
| COMPANION_SKILLS.md | other skills/tools to install so every app matches the desktop app |
| MISTAKES.md | the rejection history behind the rules |
| PLAYBOOK_5OCLOCK.md | the full 18-shot worked plan: how every shot is built, voiced and cut |
| lib/ | toonlib.py (toon materials, lin(), outline hull, lathe, mesh helpers; exec'd by build scripts), vrm_pose.py (VRM rider seating, IK grip, finger curl) |
| scripts/ | qa_frames.py (contact sheet + crops + numbers vs the locked frame), run_shot.ps1 (timed full shot on the render box), mix_ref.py (voices + score + SFX by time) |
| templates/ | STATE.md, SHOT_RULES_template.md, storyboard_shot.md, qa_log.md, dialogue_table.md |
| companion (../companion/) | the user's other skills to install alongside (COMPANION_SKILLS.md) |
| reference/5oclock_ep1v3/ | the real approved shot code (01-04), cast builder, hero toon builder, SHOT_RULES, storyboard, research (reels, music reference, Granite Waves study), decisions, quality-bar frames (*.jpg) |
