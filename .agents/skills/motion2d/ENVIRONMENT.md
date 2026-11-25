# ENVIRONMENT: machines, models, tokens, delivery

## Compute
- **Render box**: the user's home Asus TUF F17 (RTX 3050 4 GB), folder `C:\Users\cross\Downloads\xc`,
  Blender 5.0.1 portable `xc\blender501\blender.exe` (works on driver 566.07) + VRM add-on 4.10.5.
  The office laptop (`C:\Users\Developer\...`) has no usable GPU: never render there. Both machines can show
  the same name; check the folder PATH before starting a remote session.
- **Cloud** (no GPU): `pip install bpy` for headless EEVEE via software GL. Use it to write and logic-test
  scripts on 2-3 low-res frames; never for full renders when the box is online.
- One Blender render on the GPU at a time. Other threads/projects may queue renders: take turns, slot short
  renders between their chunks.
- Never change power/sleep/driver settings; ask the user (the box is set to never sleep on AC).
- If a usage limit stops work, resume when it refills; `STATE.md` holds everything needed.

## Model routing and tokens
| work | Claude | Codex/OpenAI | other |
|---|---|---|---|
| story, storyboard, character design, build scripts, every QA verdict | Opus, high effort | GPT-5-class, high reasoning | best available |
| render queues, encodes, file copies, downloads, frame pulls | Sonnet/Haiku subagent | mini | small |
- One contact sheet per probe (not 10 look-tests), crops only where needed, no page-text dumps, no progress chatter.
- At most 2 heavy threads at once.
- Big binaries (character .blend 14-16 MB each, VRMs) stay in the shared project folder, not in git.

## Delivery
- Shot clips and PNGs to the user's thread the moment they finish (notification). Max ~6 attachments per message.
- Files > 20 MB: push to the project's git branch and give the raw link
  `https://github.com/<owner>/<repo>/raw/<branch>/<path>`.
- Names: `NN_name_vK.mp4`, never overwrite a seen version.
