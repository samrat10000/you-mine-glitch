# PIPELINE: exact build recipe (toon-anime default)

## Folder layout per project
```
<project>/                    e.g. xc\anime-5oclock\
  STATE.md  SHOT_RULES.md  DECISIONS.md  MISTAKES.md  WORKING.md  QA_LOG.md  storyboard.html
  assets/   toon_<hero>/ (build_<hero>.py, <hero>_toon.blend, SOURCES.md)   cast/ (*.blend + previews)
  ep<N>/NN_name/src/          build_sNN.py  paint_bgNN.py  comp_sNN.py  run_full.ps1  README.md
  ep<N>/NN_name/vK/           NN_name_vK.mp4 + 4 PNGs + crops (never overwritten)
```

## Per shot: 4 scripts
1. **build_sNN.py** (Blender, `blender -b --python build_sNN.py -- <ABS outdir> <scale> <frames|all>`):
   - First lines: `argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]`
     (works in blender.exe and in the `bpy` pip module).
   - `exec` the shared `lib/toonlib.py` (toon(), emis(), outline(), mesh_obj(), lathe(), ellipsoid(), empty()).
     If the shot needs another sun direction, replace the SUNV line in the source string before exec.
   - Build the set in a local frame (an empty like TOWN/ROAD rotated to the slope) so helpers work in
     local coordinates. Reuse earlier shots' builders by extracting their functions with `ast` (see
     reference 04: lib04 generated from build_s03.py) rather than copying code.
   - Load characters from their approved `.blend` (append the collection), set rig rotation_mode XYZ,
     store rest quaternions, pose per frame with rest-local deltas, IK for hands, ground offset for feet.
   - Animate: characters on twos (`fpose = f - (f-1) % 2`), camera every frame.
   - Render settings: EEVEE, film transparent, Standard view, 16 TAA, 1080x1920 x scale, PNG RGBA.
   - Write `cel_NNN.png` (+ extra passes like `refl_NNN.png`, `uv_NNN.png` 16-bit) and `meta.json` with
     SUN_SCREEN, camera data per frame, projected polygons the comp needs (glass, mirror) and bboxes of
     hands/faces/feet for the QA crops.
2. **paint_bgNN.py** `<outdir>/meta.json`: numpy sky, sun, clouds, ridges, far layers at 110% size -> PNGs.
3. **comp_sNN.py** `<celdir> <outdir>`: the composite stack in RULEBOOK R10, frame by frame, 4 processes.
4. **run_full.ps1** (render box) / `run_full.sh` (cloud): build -> paint -> comp -> encode, logs per step.
   Writes into new folders only (refuse to overwrite an existing `full\`).

## Encode
`ffmpeg -y -framerate 24 -i fullc/%03d.png -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p NN_name_vK.mp4`

## Probe -> full
- Probe: `build ... 0.5 1,24,48,72` then comp those frames, then `qa_frames.py`.
- Full: only after the probe passes QA.

## Timings (reference hardware)
| step | RTX 3050 laptop (Blender 5.0.1) | cloud 4 CPU (bpy, software GL) |
|---|---|---|
| EEVEE cel 1080x1920 | 0.6 s/frame (+ ~25 s first-run shader compile) | 10-25 s/frame |
| paint bg | 6-10 s per shot | 10 s |
| comp | ~3-4 s/frame | ~3-5 s/frame |
| 96-frame shot with reflection pass | build ~150 s + comp ~380 s | ~45 min |
So: scenes are written and logic-tested in the cloud at low res on 2-3 frames; every full render runs on the GPU box.

## Characters from VRoid (the cast pipeline)
1. Blender + VRM add-on (saturday06, MIT; v4.10.5 for Blender 5.0.1, installed as an extension zip:
   `bpy.ops.extensions.package_install_files(filepath=vrm_ext.zip, repo='user_default')`).
2. Import the CC0 VRM, convert MToon to the toon node chain (keep the base texture, add the 2-tone ramp),
   inverted-hull outlines (multiply width by camera distance rule), delete hidden faces under new clothes.
3. Proportions by pose-bone scale (kids table in RULEBOOK R2), then scale the armature to the target height
   from evaluated mesh bounds.
4. Costume pieces measured from body bands, bone-parented (`parent_type='BONE'`, keep world matrix).
5. Save `<name>.blend` + `<name>_preview.png`. Review the preview sheet (G3).
Reference: `reference/5oclock_ep1v3/assets/build_cast.py` and `build_sam.py`.

## Creatures/animals
Real CC0 GLB with its own clips -> subsurf 2 + toon + hull 0.0035 m -> blend clips per bone with quaternion
slerp -> toes locked to surfaces every frame. Reference: `reference/5oclock_ep1v3/01_speaker/build_s01_v4.py`.

## Reflections and mirror worlds
- Curve mirror / screen: emission UV pass + painted insert mapped in the comp (convex tan warp for a curve mirror).
  Reference 02_mirror (build_s02.py, comp_s02.py, paint_night.py).
- Shop window with a late reflection: holdout glass (0.58 holdout / 0.42 dim interior emission), mirror
  camera = camera reflected across the glass plane, a late twin rig (N frames behind) visible only to that
  pass; flip horizontally in the comp and insert inside the projected glass polygon where cel alpha < 1.
  (EEVEE planar probes do not work headless: don't use them.) Reference 04_ride.

## Render box routing
Cloud writes and tests scripts, pushes to the git branch; the render box pulls, runs `run_full.ps1`, pushes
`pc_test/NN_name_vK/` (mp4 + key PNGs + crops); the cloud pulls, copies to the shared project folder and
delivers. Use absolute outdirs with blender.exe (a relative one wrote to `C:\test\`).
