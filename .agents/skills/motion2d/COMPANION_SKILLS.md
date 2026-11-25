# COMPANION SKILLS AND TOOLS: give every app the desktop app's toolbox

Part of why the Claude desktop/cloud runs gave better results than the VS Code extension: they had more
skills and tools available. Install these wherever you run `/motion2d`.

## 1. Bundled here (copied by the installer into ~/.claude/skills and ~/.codex/skills)
`companion/` holds the user's own account skills:
| skill | use in a reel |
|---|---|
| ig-reel | hooks, script and beat sheet from a raw idea (P1) |
| ig-viral | what's working now in the niche, outlier multiples (P1 research) |
| ig-caption | the caption, search terms, hashtags (delivery) |
| ig-human | strip machine fingerprints from captions/scripts |
| glb-vehicle-builder | stylized vehicles/props as GLB with ink outlines |
| remotion-best-practices / remotion-render | code-driven titles/motion-graphics inserts if needed |

## 2. Built into Claude (turn on, don't copy)
claude.ai Settings > Capabilities > Skills: enable **skill-creator**, **deep-research**, **pdf**, **docx**,
**pptx**, **xlsx**. Claude Code in VS Code uses the same account skills once enabled. Public copies also live at
https://github.com/anthropics/skills (install into `~/.claude/skills/`).

## 3. Tools (install once on each machine)
| tool | why | install |
|---|---|---|
| Blender 5.0.1 (+ VRM add-on 4.10.5) | cel renders, VRoid characters | blender.org portable; add-on zip from github.com/saturday06/VRM-Addon-for-Blender/releases |
| Python 3.10+ with numpy scipy pillow pypng | paint, comp, QA | `pip install -r motion2d/requirements.txt` |
| ffmpeg | encode/assemble | on PATH |
| @gltf-transform/cli (Node) | decompress meshopt GLBs | `npx @gltf-transform/cli copy in.glb out.glb` |
| earshot | "listen" to audio and quote numbers | source tarball in the project's shared tools folder (`tools/earshot-src.tgz`), `pip install -e earshot[mcp]`, then `claude mcp add earshot -- python -m earshot mcp` |
| Claude in Chrome extension | reference research, ElevenLabs/Flow Music in the user's signed-in browser | Chrome Web Store; the user signs in to sites |
| GitHub access | delivery links, render-box handoff | `gh auth login` or the app's GitHub connector |

## 4. Check at the start of every session
1. The agent can open a PNG and describe it (image viewing). 2. `blender -b --version` works. 3. `python -c
"import numpy, scipy, PIL, png"` works. 4. `ffmpeg -version` works. If any fails, say so before building.
