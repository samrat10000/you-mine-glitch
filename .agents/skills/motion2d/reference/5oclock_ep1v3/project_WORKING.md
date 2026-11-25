# WORKING.md : everything so far (handoff log)

Written 2026-11-22. Project: Sam's money automation at peek, anime / Night Terror / "5 O'CLOCK" branch. This file is the memory. Update it as you work.

Codex follow-up, 2026-11-22. [REEL_RESEARCH.md](REEL_RESEARCH.md) contains the live comment review, public counts, runtime checks, Japanese and cross-platform comparisons, and a test brief. The road reel has 398K views. A same-creator reel of nearly identical length has 34.4M. Numbered logs are a format worth testing. Public views and current followers cannot tell us whether numbering, watch time, or an app funnel converted viewers. The local `story/` folder was still absent.

## 0. What Sam asked (in his own words, shortened)
1. He shared a reel (Granite Waves) and said the animation is 2D, not 3D, and "looks so damn good". Wanted: what art form it is, the channel and its other reels, how the creator makes them.
2. He loved the voice and asked for a very deep analysis of it, to reproduce for our dialogue.
3. He said: we are not copying anything. We take inspiration from the art form (purely anime style). Our own characters, scenes and story. A unique story comes first, before characters. He likes Chainsaw Man, Pacific Rim, Kaiju No. 8. Setting: a Japanese place, Sam is the main character. A "fabulous and crazy" plot that can have millions of reels around it. Wanted 5 story ideas.
4. He shared a second reel (night road with a black void). He said it feels like an alternate universe communicating with Earth, and that "we are going to revolve around this idea", one concept that people engage with a lot. He wants a lot of research first: what viewers see, what is missing, what should be there so people are amazed. "Use the web at the fullest, use the Insta at the fullest."
5. He wants everything tracked in this folder so it can continue in Codex (tokens are low; reset after about 1 hour).

## 1. Story concept in play (from the story thread, not by me)
"5 O'CLOCK": a Japanese town, lone survivor (Sam), a loudspeaker song at 5 PM answered by another Earth, kaiju, rules, suspense. The story files are written by the thread "Pitch 5 anime story ideas" and are copied into `story/` here when ready. Check there first.

## 2. Reel 1: Granite Waves (art form)
- It is hand-drawn 2D anime in a vertical (9:16) "micro-drama" series. Flat cel colour, thin dark line, muted palette with one accent colour (red jacket), soft heavily blurred painted backgrounds, long held poses, tiny movements (eyelids, hair, breath), burned-in subtitles in the lower third, Matt Lange "Punish Me" used as music on other reels.
- Channel: granitewavesseries 1.2M followers, 98 posts. Creator Tezeze (tezeze_art, 630K). Streaming only on the Ryuu app, which funded season 1. Top reel 58.5M views. Highlights: Start here, Pilot, Zima, #dtiys 100K, Elya, VA tutorial, VAs.
- Making-of: a "Final vs animatic" BTS reel shows a rough pencil animatic beside the finished frame. Tool names are NOT confirmed (no making-of found, web search found nothing). Likely: storyboard, pencil animatic, digital inking, flat fills with one shadow layer, painted/blurred background, compositing grade. Frame rate not measured (likely 12 to 24 fps with holds).
- Full doc: `granite-waves-study.html` (also published as an Artifact: https://claude.ai/artifact/YYZsuSf6ZoRv7igTrz2iZD).

## 3. Reel 1 voice analysis
I cannot listen. I measured the audio in the browser (pitch, loudness, spectrum) while the reel played. Music is mixed in, so numbers are approximate.
- Pitch about 70 to 105 Hz, mostly 80 to 95 Hz (low male voice).
- 60 to 90 percent of the energy below 250 Hz, spectral centre 200 to 450 Hz, almost nothing above 6 kHz: very warm and dark, close mic, rolled-off highs.
- Line peaks RMS 0.17 to 0.29, tails fall to 0.02 to 0.06: starts with weight, then fades. Tired, weary delivery.
- Pacing: lines of 1.5 to 3 s, gaps 1 to 3 s. Silence is part of the acting.
- No audible room echo (dry booth).
- Real human actors almost certainly: the channel credits named pro VA Sarah Natochenny on Ep 2, has "VAs" and "VA tutorial" highlights, and a sibling series credits a VA and a sound designer.
- Recipe for us: cast a real person with a low tired close-mic voice, speak quietly with weight at the start of lines and fade, leave a second of silence between lines. Record about 10 cm from the mic with a pop filter in a quiet small room. Mix: cut under 70 Hz, lift 150 to 250 Hz, roll off above 6 to 8 kHz, light compression, no reverb, duck music 8 to 10 dB under lines.
- Sam wants nothing that sounds AI-made, so use a real voice.

## 4. Reel 1 verdict for Night Terror
- Reproducible in Blender with Grease Pencil: flat cel fills, thin line, blurred background layer via compositor defocus, one accent colour per scene, cold colour grade, big bold subtitles.
- Needs hand-drawn key poses and long holds (animate on twos, small moves) so it does not look generated.
- Do not copy characters, logo or titles. Technique only.
- Next step suggested: one test shot (character in profile, held pose, blurred window, one red accent, real voice line), compare against `frames/f1_risk.jpg`.

## 5. Reel 2: "起秋" by @pseudohuasca
- 13.7 s, 1080x1920. One continuous locked shot of an empty night road (Taiwan-style: red curb line, double yellow centre line, streetlights, trees). No dialogue, no on-screen text.
- Beat map (approx., from frames at 20/40/60/80/100 percent): empty road, then a thin dark figure far down the road at the bend (about 20 percent), then a black diamond-shaped void with fragmented jittery edges and dark shards on the asphalt (about 60 percent), then the void fills about a third of the frame and eats the road (about 80 to 100 percent).
- Suspense method: ordinary footage first so every change feels wrong, tiny far thing so you lean in, slow escalation in one place, warm lights vs pure black (missing reality), no explanation, no cut away.
- Sound: could not be measured (audio reader returned silence). Caption credits Ableton for sound design, so a designed drone or glitch bed is likely.
- Made with: Ableton, TouchDesigner, After Effects, Blender (credited in caption).
- Story use: another reality leaking in as one small wrongness in a normal place. Frames: `frames/r1` to `r4`.

## 6. Instagram research (so far, read only)
Method: hashtag pages (only hashtags work; text keyword searches return nothing), account profile reels tabs (they show view counts), reel pages (caption, likes, comments).

Findings:
- Numbered-entry horror is the strongest serial format found. slumberspeak (156K followers, only 298 posts, captions say "Original Work - no Ai" and "Human made - no generative AI used") posts 8 s reels titled "entity 999000111 logged" and "Quest Log: 333 (with coordinates)". One reel got 4.9M views, others 996K and 473K, while typical posts get 4K to 20K. Spiky: the hit is a tiny, numbered, repeatable "log" format over looped real nature footage with a glowing glitchy entity. Also credits tools openly (After Effects, TouchDesigner, Ableton, Illustrator) and says no AI. Open credit builds trust.
- Animated horror novel format: toonimated (217K followers, 795 posts) posts black-and-white manga-style panels with burned-in subtitles that read like a novel being narrated; grid views 2.1M, 87K, 61K, 41K, 23K. "Metamortis" caption: psychological horror with metaphysical mystery, "a world whose rules defy understanding". It funnels to a YouTube channel (link in bio).
- Serial teasers from small accounts: dreadful_tree "You have been selected. Participation in the spiritual assessment is expected. Further instructions will follow. EPISODE 01 COMING SOON." (only 268 likes: a teaser with no proof of a world gets little).
- Candle Cove style retellings (horrorwithaura, 3.5K likes) show reused creepypasta underperforms. Original lore does better.
- Dreamcore / liminal tags are full of generic aesthetic posts, many AI-labelled (for example liminalhabitats tagging an AI tool, liminalsp3ces tagged "AI content"). Comments are things like "I like this side of instagram", "plz do not wake me", "your work is so good, very unsettling". Viewers want a feeling, not a story, and the generic pool is saturated. A real story with rules is a gap.
- Granite Waves shows the anime route: 58.5M on the season welcome reel, series tagged with episode numbers, funded by a streaming app, each reel is a clip from an episode with one emotional line burned in as subtitle.

Gaps still open for the next researcher (Codex or Claude):
- Comment themes on the biggest reels (comments did not load in my reads). Open each reel in Chrome, scroll the comments, note repeated asks like "part 2", "what is this", "I need the full story".
- Retention patterns: first-second hook, loop endings, "Part N" numbering, pinned comments. Not yet measured.
- Anime/Japan horror accounts (the hashtags #animehorror and #foundfootage returned nothing in my reads; try #japanhorror, #urbanlegend, #yokai, #kaiju, #shinjuku, #showa, #hououji).
- Follow-conversion: measure attributed follows per reel in creator Insights. Public views and current followers indicate relative scale only. Granite Waves has a visible episode catalog and app destination. Their conversions cannot be inferred from these counts.
- Non-IG research (YouTube, TikTok, Reddit r/nosleep, analog horror channels) not done.

## 7. What was NOT done / honest limits
- I cannot hear audio; the voice numbers are measurements, not listening.
- Tools used by Granite Waves are inferred, not confirmed.
- Reel 2 sound unmeasured.
- Story ideas were written by a different thread, not here.
- Nothing was liked, followed, commented or posted.

## 8. Next steps (suggested order)
1. Read the story files in `story/`.
2. Finish the open research gaps in section 6 (comments and retention first).
3. Lock the hook: one small wrongness in a normal place (the 5 O'CLOCK loudspeaker song), numbered logs/entries for serialization, original lore with rules.
4. Make one test shot in Blender Grease Pencil in the Granite Waves art style (only the style), with a real voice recorded for the line.
5. Keep updating this file.

## 9. Ep1 v2 render + assembly (2026-11-22, Claude on the PC)
Status: picture done, sound blocked (no Flow piano take for 5 O'CLOCK on the PC yet).
- Shot 003 (toon 3D Sam): `toon3d/scripts/anim_003.py` updated (v1 kept as `anim_003_v1_backup.py`). The reach now has one IK in-between at f31 with the elbow down at the side (the earlier attempts jutted the elbow sideways). The hood is at full size (back 1.45x, roll 1.1-1.15x). The shot is 84 f / 3.5 s on twos, with the action ending at 3.0 s and the last drawing held. Transparent 1080x1920 frames are in `toon3d/003_v2_alpha/`.
- Build kit from samrat10000/dead-roads-ep2, branch `claude/project-thread-31g858`, folder `anime-5oclock/ep1v2/pc/`. Copied to `ep1v2/build/` with pycairo/numpy/scipy/pillow installed, VSCO Marimba+Glock in `build/vsco`, and SFX (crows, wires) in `build/snd`.
- Frames: `ep1v2/build/fr001`-`fr005` (120/84/84/108/108). 005 used NOTE_T=1.9, BLACK_T=2.6. 003 was composited with comp003.py.
- Cuts at 0 / 5.0 / 8.5 / 12.0 / 16.5 / 21.0 s. Silent clips: `ep1v2/build/00N_<name>_v2_silent.mp4`. Full cut: `ep1_v2_full_silent.mp4` (61 MB), plus a small preview.
- Review: 24 full-res stills are in `ep1v2/stills_v2/`. The review page + clips + stills are in `ep1v2/review/`, published privately at https://claude.ai/artifact/V94KbrwHsd8HBm3CVEuv1i and pushed to GitHub (same branch, `anime-5oclock/ep1v2/review/`, commit 94d4813). Git worktree used for the push: `xc/_wt_ep1v2`.
- Audio: voice takes A/B for N1, N2, S1, P1, S2 are in `ep1v2/audio/`. Still to do: add the Flow piano takes there, pick the one whose piano starts in the first second with the clearest rests, run `python mix_v2.py <flow> ../audio mix_v2.wav`, loudnorm I=-15 TP=-1.5, then mux the per-shot clips + full cut with sound.

## 10. How Sam works from now on (2026-11-22)
- All work happens in `C:\Users\cross\Downloads\xc`. Sam switches between Claude accounts and tools (VS Code Claude extension, the Claude app on this PC, project threads) without losing context. These files ARE the context.
- Two files, both in `xc\anime-5oclock\`:
  - `WORKING.md` (this file) is the log of what was done: what, where the files are, how to rerun. Every session appends a dated section at the end. Never rewrite other sessions' sections.
  - `DECISIONS.md` holds the decisions made (and why) plus the current to-do list (what still needs doing, in order). Update it whenever a decision is made or a task is finished or added.
- A session works until its tokens run out, and before that it writes its progress into both files. Sam then tells the next Claude (another account or thread) to pick up from these files.
- Every new session reads `WORKING.md` (at least sections 0, 9 and the latest ones) and `DECISIONS.md` first, before doing anything.
- Teaser jobs on this PC have priority. Run renders at below-normal priority and never stop the teaser's jobs.

## 11. 2026-11-23: quality review (Claude, VS Code extension)
- Sam rejected the Ep1 v2 animation quality, so the "picture done" status in section 9 is superseded. Compared stills from 001-005 with the saved reference stills; diagnosis, open questions and new to-do order are in DECISIONS.md "Added 2026-11-23".
- No Chrome tool was available in this session, so the reels were not watched in motion.
- Corrected paths: README_PC.md is in `ep1v2\build\` and `xc\_wt_ep1v2\anime-5oclock\ep1v2\pc\`; EP1_V2_SOUND_PLAN.md is in `xc\_wt_ep1v2\anime-5oclock\ep1v2\`. They are not at the paths given in the starter prompt. No 5 O'CLOCK Flow take found by filename in `xc` or recent Downloads audio.
- Files changed: WORKING.md and DECISIONS.md only. Nothing rendered, mixed, pushed or posted.
- Next: Sam connects Chrome and picks the look route for 003; then remake 003 only as v3.
- 2026-11-23 (later): Chrome connected, Sam signed in. Watched Granite Waves DeZlMh5M1jI via screenshots (findings in DECISIONS.md). Did not yet watch DeS2sH9MjFX (night road). Nothing rendered or changed besides these two logs. Next: Sam approves new storyboard direction, then 003_sam_v3.
- 2026-11-23: Made rough 7-shot storyboard for Ep1 v3: ep1v3\storyboard_v3.png (21 s: mirror 3.0, speaker 3.5, feet 2.0, hand 3.0, profile 3.0, street 3.0, answer 3.5). Generated by a PIL script, composition only, not final art. Awaiting Sam's approval/changes. Next: approved storyboard -> remake shot 4 (hand) or 5 (profile) first as the quality test, named 004_hand_v3 etc.
- 2026-11-23: storyboard script saved at ep1v3\storyboard_v3.py; opened PNG for Sam; corrections logged in DECISIONS.md. Next: storyboard_v4 (fixed story/timing) + one finished style frame of Sam.
- 2026-11-23: DONE 003_sam_v3 silent: `ep1v3\003_sam_v3_silent.mp4` (1080x1920, 24 fps, 84 f, 3.5 s, on twos), still `ep1v3\003_sam_v3_still.png`. Code: `ep1v3\build\sam2d.py` (drawn Sam, pose dict), `shot003.py` (timing, plate, grade), `run003.ps1` (below-normal CPU render, about 4 min or less, no GPU). Frames `ep1v3\build\fr003\`. shot003.py imports lane.py/lib.py from `ep1v2\build\`. Checked on sampled frames, not watched in playback. No sound. Next: Sam's verdict, then 005.

## 11. PC set up as the Ep1 v3 render box (2026-11-23, Claude on the PC)
- `ep1v3/` sources (01_speaker, 02_mirror, 03_kiriyama/src_v2, SHOT_RULES.md) were copied from branch `claude/project-thread-31g858` into `xc\anime-5oclock\ep1v3\`. Nothing local was overwritten.
- Patched every `build_s0*.py` so it reads args after `--` under blender.exe. Added `run_full.ps1` next to each `run_full.sh`. Installed pypng.
- Speed test on shot 03 (1080x1920, EEVEE): about 0.6 s per cel frame, about 3 s per comp frame, 9.5 s BG paint per shot (cloud: 25 s / 5 s).
- Run: `blender.exe -b --python build_s03.py -- <ABSOLUTE outdir> 1.0 <frames|all>`, then `python paint_bg03.py <outdir>\meta.json`, then `python comp_s03.py <outdir> <compdir>`. Or just run `run_full.ps1`.
- Notes + comped frame 42 pushed: `anime-5oclock/ep1v3/pc_test/` (commit 59529a5). Test output is in `03_kiriyama\src_v2\test\` and `testc\`.
- A stray copy of 3 test cels is in `C:\test\` from a first run with a relative path. Deleting it was blocked as a system path, so Sam can delete it by hand.
- 2026-11-23: Shot 01 (locked v4 scripts) was fully rendered on the PC in about 5 min: `ep1v3\01_speaker\src\01_speaker_v4_pc.mp4`, with frames in `fullc_v4\`. Pushed as commit 7900af9 to `anime-5oclock/ep1v3/pc_test/01_speaker_v4/`.
- 2026-11-23: Shot 01 v4b (glint fix only) rendered on the PC and pushed (b60f4e9). Sam: keep v4. The v6pc crow experiment (glide, Freestyle feather lines, breathing) is shelved locally in `ep1v3\01_speaker\src\build_s01_v6pc.py`.
- 2026-11-23: Shot 04 "Sam rides home" v1 rendered on the PC: about 8 min (build 139 s, comp 339 s). Pushed as db23340 to `pc_test/04_ride_v1/`. My critique for v2: flat contrast and no warm rim on Sam, a plain asphalt road (breaks the ground-detail rule), a soft hoodie outline. Sent to the cloud Claude.
- 2026-11-23: Shot 04 v2 (4acdb21) and v3 (c08870f) rendered on the PC. In v3 the rim is on Sam's sun-facing side and contrast p95 is up from 0.63 to 0.80. The VRoid CC0 cast pool (11 VRMs, cast sheet, cast_list.md) is pushed as de3aba7 under `assets/vroid_cc0/`. The cloud's build_cast.py ran on the PC and the 4 cast .blends were pushed as 9dea246. Look check: none read right yet (the grandma and kids read as teens, the shopkeeper as about 20). Fix suggestions were sent to the cloud Claude.
