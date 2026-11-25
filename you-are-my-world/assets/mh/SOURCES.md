# Assets & Sources: MakeHuman CC0 Anatomy Base

## Base Mesh, Rig & Weights
- **Source:** MakeHuman (`base.obj`, `default.mhskel`, `default_weights.mhw`, and `.target` morphs)
- **Origin in Workspace:** Copied from `samrat10000/money-skills` (`make-terror-night/terror-night/engine/mh/`)
- **Licence:** CC0 1.0 Universal (MakeHuman official base mesh and assets)
- **Specs:**
  - `base.obj`: 19,158 total vertices; `body` group uses contiguous vertex indices `0..13379` (13,380 vertices, 13,378 quad faces -> 26,756 triangles)
  - `default.mhskel`: 163-bone hierarchical skeleton (`root`, spine `05..01`, neck `01..03`, `head`, arms, hands/fingers, legs/feet)
  - `default_weights.mhw`: linear-blend skinning weights covering 100% of `body` vertices (`0` unbound body vertices)

## Morph Targets Used (`assets/mh/t/`)
- **Girl (`universal-female-young-minmuscle-minweight.target` + `head-fat-decr.target` + `nose-point-width-decr.target`):** Graceful slender female proportions (`~1.62 m` scaled)
- **Boy (`universal-male-young-averagemuscle-minweight.target` + `male-young-averagemuscle-averageweight-idealproportions.target` + `head-fat-decr.target` + `chin-prominent-incr.target`):** Lean young male silhouette (`~1.72 m` scaled)

## Procedural Garments & Hair (Built in `rig_mh.py`)
- Girl flared pleated A-line mini-dress (16 radial pleats + dynamic cyclic wind deformation)
- Girl 22+ layered flowing curved hair ribbon strands + crown cap
- Boy relaxed draped jacket/hoodie shell with sculpted back/shoulder fabric crease relief
- Boy 30+ layered tousled curl hair locks for crisp 3/4 rim-lit profile

