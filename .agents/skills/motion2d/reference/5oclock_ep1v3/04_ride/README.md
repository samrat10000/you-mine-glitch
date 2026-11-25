# Shot 04 "Sam rides home" (v1 sources)
- build_s04.py: scene + animation. Writes cel_NNN.png, refl_NNN.png (the late mirror pass for the shop window) and meta.json.
- paint_bg04.py <outdir>/meta.json: painted bay sky (sky04.png) plus far shore and sea (far04.png), written to the current folder.
- comp_s04.py <celdir> <outdir>: final frames. run_full.ps1 does all of it on the Asus.
- Needs ../../../assets/toon_sam/sam_toon.blend (or a copy next to the scripts).
- Shop lettering font: ipag.ttf next to the scripts if present, else Windows Yu Gothic / MS Gothic. lib04.py and toonlib_v4.py come from 03_kiriyama/src_v2 automatically.
