# WORKING: you-are-my-world

## 2026-11-25
- **P0-P2:** Copied CC0 MakeHuman assets (`assets/mh/`) and 6 reference frames (`refs/`). Authored `brief.md`, `DECISIONS.md`, `SHOT_RULES.md`, `storyboard.md`, `STATE.md`, `QA_LOG.md`, `MISTAKES.md`.
- **P3 Gate G3:** Built `ep1/01_hilltop/src/rig_mh.py`, passed Gate G3 (`assets/cast_preview.png`).
- **P4 Probes (`probe_v1` -> `probe_v2` -> `probe_v3`):** Built `paint_bg01.py`, `build_s01.py`, `comp_s01.py`, `run_full.ps1` and iterated through 3 full-res probe QA cycles.
- **P4 Master (`v1`):**
  - Applied final 4 tuning tweaks (`OMP/OPENBLAS/MKL=1`, grain `* 0.35`, cloud pulse lift, back-fold halftone sparkle).
  - Rendered 240 character passes (`45.86s`, max IK err `1.120 cm`, `footZ=0.0 cm`) + 240 optical CRT composite frames (`519.63s`).
  - Encoded `v1/01_hilltop_v1.mp4` (CRF 14, 73.7 MB) and `v1/01_hilltop_v1_IG.mp4` (CRF 18, 34.3 MB); verified `1080x1920`, `24 fps`, `240` frames (`10.00s`).
  - Ran 240-frame QA (`avg mean=0.314`, `p95=0.795`, `MAE 240 vs 001 = 0.01286`), verified contact sheet + 4 hero PNGs + clasp crop visually.
- **P4 `v2` Overhaul:** Removed Girl head-scratching gesture, added 2-bone leg IK + closed shoes, moved Boy to 3/4-back profile with 80 surface-sampled curls, dome-sculpted clouds & staggered CRT stipple (`01_hilltop_v2_IG.mp4`).
- **P4 `v3` Extreme Realism + Stardust Grain Girl + Universe Glitch:** Built `paint_bg_v3.py` (`bg_v3/`) & `fx_v3.py` (`v3/`), passed `probe_v6` (`MAE=0.01843`), rendered 240f `v3` (`avg mean=0.279, p95=0.741, 0 black/frozen`), encoded `01_hilltop_v3_IG.mp4`, and authored `../CODEX_MISTAKES_AND_HANDOFF.md` for Codex `v4` handoff.
