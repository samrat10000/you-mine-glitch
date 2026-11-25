---
name: "ig-reel"
description: "Write an Instagram Reel from a raw idea: hook options, spoken script, on-screen text and a timed beat sheet. Use when the user wants a Reel, short-form script, hook or voiceover."
---

# ig-reel

(Source: Jakeschincariol/instagram-agent-skill. The helper scripts hookscore.py, beats.py and hooks.json ship in the ig-reel.zip in project files; without them, score hooks and time beats by hand using the rules below.)

Turns one raw idea into a Reel that somebody finishes.

```bash
python3 hookscore.py hooks.txt              # rank your hook options
python3 hookscore.py --hook "one line"      # score a single one
python3 beats.py script.txt --target 30     # timed beat sheet before you shoot
```

## Before you write

1. Read `~/.claude/instagram/voice.md` if it exists. That is the user's voice profile. If it does not exist, ask for three of their own reels, infer the voice, and write the file.
2. Read `hooks.json` in this folder if present: 26 hook formulas, each with a template, a filled example, the on-screen version, what it is for, and how it gets ruined.
3. If the idea is thin, do not pad it. Ask one batched question: what happened, to whom, and what did it cost or return. A Reel needs one specific true thing.
4. If `~/.claude/instagram/swipe.md` exists, read it. It is the user's own evidence about which formulas work in their niche right now.

## The shape

```
0:00 - 0:02   HOOK        the claim. Spoken line and on-screen line, written
                          separately. Motion in the first frame, not a static face.
0:02 - 0:07   THE STAKE   why this matters to the person watching. One line.
0:07 - ...    THE BODY    one idea per beat, and the frame changes every beat.
LAST 3s       THE PAYOFF  deliver what the hook promised, then the single ask.
LAST LINE     THE LOOP    echo one word from the hook so the replay lands clean.
```

Length: 15 to 45 seconds is the working range. Under 7 seconds the loop counts inflate and nothing else does.

## The loop

1. Pick three hooks from different formulas, each with a spoken line and an on-screen line.
2. Score them. If the top one is under 50, you do not have the hook yet.
3. Write the script on the winning hook in plain spoken language: contractions, short lines.
4. Time it. Fix a hook past 3 seconds, any beat over 4 seconds, runs of beats with nothing concrete, no loop.
5. Humanize it with /ig-human before showing it.
6. Print the script in a fenced block, the on-screen text as a separate timed list, then a REEL READY receipt (hook, length, beats, cards).
7. Never publish. The user shoots and posts it. On "yes", append to `~/.claude/instagram/log.md` with date, formula and first line.

## On-screen text is a separate script

- Six words or fewer per card.
- The hook card is up at frame 1, not after a beat of silence.
- Safe zone on 1080x1920: nothing above y=230 or below y=1440, keep the right 230 px clear.
- Never put the hook where the caption sits (bottom of frame).
- Burn in captions for the body. Most people watch muted first.

## Rules

- One idea per Reel.
- Numbers over adjectives. Ask for a number rather than writing around it.
- Cut the intro: no greeting, no "in this video", no logo sting.
- Change the frame every beat.
- One ask at the end.
- Never fabricate metrics, clients or outcomes. Leave `{{your number}}` and flag it.
- Do not write around a trending audio the user cannot use.