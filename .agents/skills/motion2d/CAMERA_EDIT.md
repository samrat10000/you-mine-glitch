# CAMERA + EDIT: angles, moves, cuts, joins

## Camera grammar (what this director loves)
- **No slideshow pans or sweep transitions.** Every move is motivated (follow a subject, reveal, push for tension).
- **Low angle against the sky** for hero objects/characters: lens 32-45 mm, subject in the upper-middle
  third, the low sun behind it. Slow push 2-3.5% over the shot, on ones.
- **Handheld documentary** for street coverage: eye height, micro-drift (two sines 0.3/0.7 Hz, 0.15-0.3%
  of frame), late reframes, as if someone in the street is filming. Never drone-smooth.
- **Side-on tracking at hub height** for riders/runners (camera 0.5 m up, pitch ~8.5 deg, lens 32), the
  subject overtakes the camera at the end (camera decelerates, subject doesn't).
- **Crash zoom** up and over an occluder to a face/creature, then a fast pull-back. Camera stays above occluders.
- **Tyre/ground cam**: 20 mm on the ground at the wheel.
- **Insert shots** over the shoulder (phone, notebook, clock) with shallow depth of field.
- **Whip pan** with 2-3 motion-smear frames (directional blur 30-60 px) between two framings.
- **Scale shot**: eye-level wide, then slow tilt up; foreground person tiny at the bottom, parallax layers.
- **Fly-through**: one continuous move at walking height weaving between frozen people; the camera is the only thing moving.
- Planar reflections, mirrors and glass give extra "angles" inside one shot (the curve mirror is a second camera).

## Shot length and rhythm
- 2-5 s per shot; ritual/montage beats 1.1-1.2 s each, cut on the beat.
- One idea per shot. The wow detail is visible for at least 12 frames.
- Hardest shots get built first as 2 s tests if the plan says so (fly-through, kaiju reveal).

## Cuts and joins (how shots connect)
- **Continuity contract** per cut, written in the storyboard: light direction, time of day (clock on
  screen moves forward only), hero costume and props (bag on the handlebar), screen direction (left->right
  stays left->right), speed (a rider never slows across a cut unless the story brakes).
- **Match cuts**: shape (round speaker horn -> round curve mirror), motion (leaf exits right -> next shot
  leaf enters left), sound (clock flip lands on the first chime note in the next shot).
- **Cut on action** (a hand starts the move in shot A, finishes in shot B, overlap 2-4 frames).
- **J-cuts and L-cuts** for voices: a line starts 6-12 frames before its shot or carries over the cut.
- **Hard cut to black** only for the stinger; a black beat is <= 0.5 s before a stinger (a longer black gap
  was hated in the teaser).
- No crossfades between story shots. No title cards over the best shots; a small end card on black only.
- Stamp (optional, series format): `KIRIYAMA · DAY 001 · 17:00:SS` small, top-left, low contrast.

## Edit build
- `timeline.json`: shot list with frame ranges at 24 fps, line start times, music markers. Picture, voice
  and SFX all read the same file.
- Assemble from approved full-res PNG frames (not from mp4s) to avoid double compression; apply the one
  grade + grain once at the end.
- Final encodes: `<show>_epN_vK.mp4` (crf 14 master), `_IG.mp4` (crf 18, -14 LUFS, AAC 320k), `_phone.mp4`.
- Run the G6 checks: frame count = timeline, no black frames except the planned ones, cut frames match.
