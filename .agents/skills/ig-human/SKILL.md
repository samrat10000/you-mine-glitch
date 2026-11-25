---
name: "ig-human"
description: "Strip machine fingerprints (em dashes, slop words, invisible characters) from captions, scripts and replies and check them before they go out. Use when text must sound human."
---

# ig-human

(Source: Jakeschincariol/instagram-agent-skill. humanize.py, detect.py and slop.json ship in ig-human.zip in project files; without them, apply the passes below by hand.)

```bash
python3 humanize.py draft.txt --report        # clean it, show what changed
python3 detect.py draft.txt                    # score it, five checks
python3 detect.py before.txt after.txt         # prove the delta
```

## Why it matters on Instagram

Captions are short and scripts get said out loud. A written-sounding line is a big share of a 600-character caption, and a voiceover nobody could say naturally is obvious in the first take.

## Fixed automatically

1. Invisible characters: zero-width spaces and joiners, soft hyphens, BOMs, tag characters, non-breaking and narrow spaces. Delete every one.
2. Typography: em dash to comma, en dash to hyphen, curly quotes to straight, ellipsis to three dots, bullet character to hyphen.
3. The slop lexicon: delve, leverage, robust, seamless, crucial, testament to, "in today's fast-paced world", plus "stop scrolling", "in today's video", "follow for more", "tag someone who needs this", "the algorithm loves", "run don't walk". Swap for a plain word or delete.

## Flagged, rewrite by hand

- "It's not just X, it's Y" and "not only X but also Y"
- Rule-of-three triads
- One-word rhetorical question lines ("The result?")
- Video preamble ("in this video I'm going to show you")
- Emoji bullet lists
- Three or more shouted words in a row
- Hashtag walls
- Reflex bait: "follow for more", "tag someone who", "double tap if"

## The five checks (0-100, higher is more human)

| check | measures | machine looks like |
| --- | --- | --- |
| BURSTINESS | sentence-length variation | every sentence the same length |
| SPECIFICITY | numbers, names, concrete markers per 100 words | abstract nouns, no figures |
| SLOP DENSITY | lexicon hits per 100 words | stock vocabulary |
| FINGERPRINT | invisible chars, em dashes, curly quotes per 1k chars | typographically perfect |
| VOICE | contractions, person, structural tells | no contractions, staged reveals |

PASS needs overall 70+ with no check below 55 (overall = 60% mean + 40% weakest check).

## Be honest

These are local heuristics, not GPTZero, Originality or Turnitin. Never tell the user their text is undetectable.

## Order of operations

1. Clean the draft and report changes.
2. Rewrite the flagged structural lines yourself.
3. Score before and after.
4. If not PASS, fix the weakest check and go again. Five rounds means write a different draft.
5. Show the cleaned text with the score, never the score alone.