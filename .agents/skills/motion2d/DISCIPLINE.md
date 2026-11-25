# DISCIPLINE: make every agent work like the run that got "absolutely crazy"

The director noticed that the Claude desktop app gave better results than the VS Code extension, and that
Codex needed constant correction ("you are doing this wrong"). The difference was never the model alone.
It was these habits. In the desktop run they happened on their own; here they are mandatory steps.

## What the good run actually did (copy all of it)
1. **Looked at every render with its own eyes.** After each probe it opened the PNG (image Read tool), wrote
   what it saw in specific words ("the near hand rests ON TOP of the bar, fingers not wrapped"), and only
   then judged. It looked at full-size crops, not only thumbnails; thumbnails hide hands and feet.
2. **Measured, didn't trust the preview.** Mean/p95 luminance, the sun's screen position, IK error in cm,
   lowest-toe height, outline width vs camera distance. Previews lie about brightness.
3. **Researched the real thing before modelling it**: what a mamachari handlebar looks like, how Japanese
   road text reads (徐行, とまれ), kawara roof tiles, randoseru, maekake aprons, the 5 PM chime history.
4. **Used real models, never primitives, for anything organic** (the crow was rejected three times as ovals).
5. **Kept a rule book and re-read it per shot.** Every director note became a rule for all later shots.
6. **Found the root cause before re-rendering** (e.g. "the VRM rig is in QUATERNION mode, so rotation_euler
   did nothing; the rider faced backwards"). It never re-rendered hoping for a different result.
7. **Self-critiqued honestly in the delivery message** (what is great, what is still weak, what comes next).
8. **Never stalled**: sent each shot, waited ~1 min, moved on; heavy renders on the GPU box in the background
   while it built the next shot in parallel.
9. **Kept state on disk** so a new session, another account or another AI continued without loss.

## Rules for every agent
- **No building without a plan file.** `STATE.md`, the shot's card (from the storyboard) and `SHOT_RULES.md`
  must exist and be read before you write a build script.
- **Your todo list mirrors the gates.** `G4 05_ritual cut a probe 1/2`, `G4 05 hand crops`, ... Mark done only
  with evidence in `QA_LOG.md`.
- **Smallest thing too.** Every prop, pose or effect you add gets looked at in a crop before moving on
  ("have I built it exactly as planned? does it look like the photo reference?").
- **No silent downgrades** (resolution, samples, frame count, layers, detail). If you must, write why in
  `DECISIONS.md` and say it to the user.
- **No fake completion.** Never "rendered/fixed/synced/looks great" without a file path or number.
- **Failing check -> one-sentence cause -> code change -> re-check.**
- **Ask little, decide well.** At most one batched question per phase. Otherwise pick the best option,
  state it, keep going.
- **Never overwrite** an output the user has seen. New version number every time.

## Claude Code in VS Code (the extension) - extra constraints
- Start with `/motion2d ...`. If the extension doesn't list the skill: "Read
  `~/.claude/skills/motion2d/SKILL.md` and every file it lists, then follow it exactly."
- Model: the strongest available (Opus) with high effort for P1-P5 and every QA verdict. `/model` to switch.
  Sonnet only for render queues, encodes and file moves.
- **Image viewing must work**: the agent must open PNGs with the Read tool. Test once at the start: render or
  open any PNG and have it describe it. If it can't, stop and tell the user (QA is impossible blind).
- In Claude Code, `/skills` lists what is installed and `/plugin` browses the org catalog; compare with
  `COMPANION_SKILLS.md`. Install the companion skills into `~/.claude/skills/` so the extension has the same
  toolbox as the desktop app. Project memory doesn't exist in the extension: `STATE.md`, `SHOT_RULES.md`,
  `DECISIONS.md` replace it, so keep them current after every step.
- Run long renders as background shell jobs, keep working, read logs when done. Never `sleep`-poll.
- Before the context fills: update `STATE.md`. After compaction: re-read SKILL.md, RULEBOOK.md, QA.md,
  SHOT_RULES.md, STATE.md.
- Open the project folder (e.g. `C:\Users\cross\Downloads\xc\anime-5oclock`) as the workspace root, so paths
  in `STATE.md` resolve. Switching accounts is safe because everything lives in those files.

## Codex (CLI / IDE) - extra constraints
- Codex reads `AGENTS.md`. Start: "Run the motion2d skill: read motion2d/SKILL.md and every file it lists,
  then follow it for: <task>." Use the highest reasoning effort.
- Codex tends to build and stop without checking. Therefore after EVERY build step it must:
  1. run `python motion2d/scripts/qa_frames.py <frames dir> --ref <locked shot frame>`,
  2. open the contact sheet and the crops it writes (attach the images to its own context) and describe them,
  3. go through the Director's eye list in `QA.md` line by line, writing PASS/FAIL + reason in `QA_LOG.md`,
  4. only then continue. "It compiled" or "the render finished" is never QA.
- After every probe Codex writes a numbered self-critique and fixes the worst 3 issues before showing anything.
- Codex must not invent new looks: reuse `lib/` and the reference code parameters, change only what the
  shot needs, and log any new parameter in `SHOT_RULES.md`.
- Codex must keep going through the shot list without asking "should I continue?".

## Small/cheap model mode (Sonnet/Haiku/mini running alone)
- Follow the steps literally, do +1 review pass on every shot, copy proven parameters from the reference
  code instead of guessing, and escalate creative calls (story, new character design) to the user with images.

## Any other AI
Load `SKILL.md` as the task instruction, give it file access to this folder and the project folder. If it
can't run code it can still do P0-P2 (story, storyboard, dialogue table) and write the shot scripts for a
runner to execute.
