# SOUND + VOICE: done last, planned first

## Order
1. Picture approved shot by shot. 2. Voices recorded from the locked dialogue table. 3. Score written around
the lines. 4. SFX placed by frame. 5. Mix and master. (The dialogue table exists from P2 so the animation
leaves room for each line.)

## Dialogue
- Sparse on purpose: about 1 line per 5-6 s (11 lines in 63 s). Pictures carry the story.
- Table columns: time (s), shot, who, line, delivery (template `templates/dialogue_table.md`).
- **Narrator**: deep, warm, older-but-not-old man, close to the mic "like telling you a secret", unhurried.
  Opens, bridges acts, and closes with the rule/question.
- Characters: one-two words where possible ("...Hello?", "Mom...?"). Whispers stay close and dry.
- Voice recipe measured from the art-form reference: low, tired, close-mic; 60-90% of the energy below
  250 Hz; weight at the start of a line, then a fade; lines 1.5-3 s with 1-3 s gaps (silence is acting).
  Mix: high-pass 70 Hz, +2-3 dB at 150-250 Hz, roll off above 6-8 kHz, light compression, dry (no reverb).
- Takes are named `<LINE>_takeA.mp3`, `_takeB.mp3`; `scripts/mix_ref.py` uses the first per prefix, so put the chosen take first.
- Double/mirror character: the hero's own take, processed drier, closer, ~0.5 semitone lower, half a beat early.
- Crowd in unison: 8-20 takes layered with 10-40 ms offsets, warm EQ, slightly wrong (pitch spread 10 cents).
- PA/loudspeaker voice: band-pass 300-3400 Hz, light distortion, mountain/valley echo (pre-delay 180-400 ms).
- Tool the director approved: ElevenLabs (signed in by the user in their browser; never type passwords).
  Batch every line in one session (credits are limited), tags like `[whispering, unsettled]`, generate 2
  takes, keep the best. Lip/mouth timing: mouth shape keys (A/I/U/E/O) keyed from the take's amplitude.

## Score
- Real recorded instruments only (sampled piano, strings, organ; e.g. VSCO-2 CE, Splendid Grand, Karoryfer
  CC0 libraries) or a music generator the director approved for this project (Flow Music via the user's
  browser). Never raw text-to-music AI beds of the kind the director rejected (ACE-Step versions "trash").
  Never synthesized guitar (Karplus-Strong "irritates the ears").
- Piano-led, ~65 BPM, short 3-5 note figures then 1-2 s breaths where only the ring remains; a held bed of
  low strings/organ underneath that never stops; the deepest note near the end; long dark reverb.
- **Around the lines**: the piano rests under each line, swells back in the gaps; sidechain duck 6-10 dB
  under speech; never a sudden cut-out or silence the story didn't ask for (a planned total silence, e.g.
  when the hero's battery dies, is a designed beat with room tone + one small sound like a bike chain tick).
- Diegetic motifs (the town chime) stay on top of the mix and are timed to the picture (each note = one
  visual ring).

## SFX
- Real recordings (Openverse/Freesound CC0/CC-BY, credits kept; Clipwing real-sfx). Per shot list them in
  the storyboard: crow wing flaps and claw grip, speaker click/static breath, bike freewheel tick, chain,
  tyre on asphalt, plastic bag rustle, broom on concrete, shutter rattle, kids' footsteps, train, crossing
  bell, wind, mirror crack (glass stress + tinkle), the kaiju (low infrasound swell + metal horn groans).
- Place by frame from `timeline.json`; layer close + room; no stock "whoosh" on every cut.

## Listening and mix
- Never claim how audio sounds without a listening tool reading (earshot: describe/match/realness/critique;
  quote the numbers). If no tool, say the mix still needs a human listen.
- Dialogue normalised, music + SFX ducked under it, final -14 to -15 LUFS integrated, true peak <= -1 dBTP.
- Master: `ffmpeg -i mix.wav -af loudnorm=I=-15:TP=-1.5:LRA=11 mix_norm.wav`, then re-measure the output.
- `scripts/mix_ref.py` places every element by time and prints WARNING when a line runs into the next; fix
  every warning before mastering. Cut the mastered track at shot boundaries to mux per-shot clips.
- Music analysis: detect note attacks/pitch, not just loudness (a piano was once misread as an organ drone).
