# PC render test: home Asus, RTX 3050 laptop (2026-11-23)

Shot: 03_kiriyama/src_v2, frames 1, 42 and 84 at scale 1.0 (1080x1920). EEVEE, unchanged settings. Blender 5.0.1 (`xc\blender501\blender.exe`), Python 3.12. Every process ran at below-normal priority.

## Timings
| Step | Time |
|---|---|
| Cel, per frame (steady) | about 0.6 s (frame 42: 0.61 s, frame 84: 0.59 s, from Blender's own Saved: timestamps) |
| Cel, scene build + first frame | 3.8 s warm. The very first run took 24 s in total, mostly the one-off shader compile |
| paint_bg03.py (once per shot) | 9.5 s |
| comp_s03.py, 3 frames | 9.7 s wall, so about 3 s per comp frame (includes Python start and loading the BG) |

Compared with the cloud (about 25 s per cel, 5 s per comp), cels are about 40x faster here and comp is about 1.5x faster.
Estimate for a full 84-frame shot 03: about 1 min of cels + 10 s BG + about 4 min of comp, plus encode.

## Exact commands (run from 03_kiriyama\src_v2)
```
C:\Users\cross\Downloads\xc\blender501\blender.exe -b --python build_s03.py -- <ABSOLUTE outdir> 1.0 1,42,84
python paint_bg03.py <outdir>\meta.json        # writes sky03.png + mts03.png next to the scripts
python comp_s03.py <outdir> <compdir>
```
Use an ABSOLUTE outdir. With a relative one ("test"), Blender saved the cels to C:\test\ (the drive root), not next to the script. meta.json and the .blend still went to the right place.

## Patches on the PC (local, not committed)
- All `build_s0*.py` in 01_speaker, 02_mirror and 03_kiriyama: one line inserted after `import ... sys`:
  `argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]; sys.argv = [sys.argv[0]] + argv`
  The rest of each script is unchanged, so it still works under the bpy pip module.
- pip: installed pypng (numpy, scipy and Pillow were already there).
- `run_full.ps1` next to each `run_full.sh` does the same steps: Blender build at below-normal priority, comp, then the same ffmpeg line (crf 14, slow).
  - For 03 it also runs `paint_bg03.py full\meta.json` before the comp, because run_full.sh doesn't run it and sky03.png/mts03.png are not in the repo.
  - 01's run_full.sh still points at build_s01.py/comp_s01.py (v1), not v4. The .ps1 copies that as it is.

Output: `042.png` here is the comped frame 42 (full res). I checked it once at small size and it matches the v2 look: sun, mountain, tower, rice fields, roofs, washing line.

## Shot 01 v4 full render on the PC
- Command: `set CROW_GLB=<src>\crow_tehbucket_raven_cc0.glb` (the repo's GLB imported directly, no gltf-transform step needed), then `blender.exe -b --python build_s01_v4.py -- <ABS>\full_v4 1.0 all`. That took 52.5 s for 72 cels including setup, and printed SUN_SCREEN 0.5762 0.6935.
- `python paint_bg.py bg_v4.png 0.5762 0.6935` took 6.3 s. `python comp_s01.py full_v4 bg_v4.png fullc_v4` took 218 s for 72 frames (about 3 s per frame).
- Encode: crf 14, slow, giving `01_speaker_v4_pc.mp4` (3.0 s, 18.5 MB). Full-res frames 001/024/048/072 are next to it.
