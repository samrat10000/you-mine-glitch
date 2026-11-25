---
name: "ig-viral"
description: "Find reels that are working right now in the user's niche, rank them by outlier multiple, name each hook formula and build a swipe file. Use for what's working, viral research or swipe files."
---

# ig-viral

(Source: Jakeschincariol/instagram-agent-skill. swipe.py ships in ig-viral.zip in project files.)

The research skill. Run it monthly, not daily. Formulas last a season.

```bash
python3 swipe.py captured.tsv --out ~/.claude/instagram/swipe.md
```

## The core idea

Raw views are not evidence. Rank on the outlier multiple: views divided by that account's own recent median. Above 3x is a signal; below 1.5x teaches nothing. Collect accounts within about 10x of the user's own size.

## Step 1: pick accounts

Ask for 6-12 accounts or propose them for approval: 4 direct (same niche, slightly ahead), 4 adjacent (different niche, same audience), 2-4 outsized (format only). Also ask the user to open their own Saved collection.

## Step 2: look

Use whatever browsing tool the session has.

- Never log into Instagram for the user and never ask for a password.
- This is reading, not scraping: about ten accounts, a dozen reels each, at human speed. No crawlers, no scraping services, no background loops.
- Copy the formula, never the video. Attribute every row.

Capture per reel: account, followers, median (middle of last 12 reels), views, hook (verbatim first line), on-screen text, length, cta.

If Instagram will not show enough, YouTube Shorts shows public view counts and auto-captions; take caption words under 3.0 s as the spoken hook.

## Step 3: rank

Fill a TSV (account, followers, median, views, hook) and run swipe.py. It computes the outlier multiple, names the hook formula, scores the hook, and compares the top third with the bottom third.

## Step 4: report carefully

1. Which formulas over-index in the top third, with counts.
2. What the top third share structurally: hook length, visual payoff, first-frame motion, where the ask is.
3. The unclassified hooks, read by hand; they may be a new formula.

State sample size and confidence plainly. Forty reels across six accounts supports a claim; twelve does not.

## Step 5: make it shootable

For the top three formulas, write the user's own version (their story, their number) and hand each to /ig-reel. Write the swipe file to `~/.claude/instagram/swipe.md`.

Nothing is posted, followed, liked or messaged. It reads.