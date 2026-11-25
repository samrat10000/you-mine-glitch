---
name: "ig-caption"
description: "Write and lint an Instagram caption: the line before the more cut, body, one ask, search terms and up to five hashtags. Use when a reel or post needs its caption or hashtags."
---

# ig-caption

(Source: Jakeschincariol/instagram-agent-skill. caption.py ships in ig-caption.zip in project files.)

```bash
python3 caption.py caption.txt --keywords "client proposals,agency pricing"
```

It prints the first 125 characters in a box, the way the feed shows them before "... more". Read that box first.

## Decide the job first

- Job A, the video already hooked them: a Reel carries its own hook. The caption is not a second hook. Its job is the ask, the context for it, and the words people search.
- Job B, the caption is the content: photo, single image, carousel cover. Line one is the hook, concrete and short, cut off at a cliff.

Say which job you are writing and why.

## Shape

```
Line 1      125 visible characters. Job A: the ask. Job B: the hook.
            Never a greeting, hashtag or emoji as the first character.
Body        2-6 short paragraphs with white space. Search terms live here.
The ask     one. Comment a keyword, save it, or DM.
Hashtags    up to five, on their own line at the bottom, or none.
```

Limit 2,200 characters; 600 that deliver beat 1,800.

## Hashtags

Instagram capped hashtags at five per post on 18 December 2025. They are topic labels, not a reach lever. Cut #viral, #fyp, #explorepage, #foryou.

## Search terms beat hashtags

Instagram search reads caption text. Put the phrase the user wants to be found for in a normal sentence. Ask for two or three terms.

## Rules

- No link in the caption. Bio or DM.
- One ask.
- Keyword asks use one typeable word, said out loud in the video too (Comment CONTRACT).
- Write the first comment separately if there is a link.
- Emoji as punctuation, not decoration (under 4 per 100 characters).
- Write alt text for carousels and photos.

## Loop

1. Decide Job A or B and say which.
2. Draft.
3. Run /ig-human on it.
4. Lint with the user's search terms. Fix every FAIL, decide every WARN out loud.
5. Print the copy-ready block, then a CAPTION READY receipt (job, visible chars, ask, hashtag count, search terms).

Nothing is posted. The user pastes it.