---
name: "remotion-render"
description: "Export a Remotion video, still image or OpenTimelineIO timeline from the command line. Use when the user explicitly asks to render or export a Remotion composition."
---

(Source: remotion-dev/skills v4.0.545. The extra pages transparent-videos.md and opentimeline.md ship in the remotion zip in project files.)

## General rendering strategy

Use Remotion's bundled browser for rendering, including compositions using `<HtmlInCanvas>`. Let Remotion download or update it. Do not set `--browser-executable`, `browserExecutable` or `chromeMode` unless the user asks.

```
npx remotion render [composition-id] out/video.mp4
```

Always pass the composition ID; list them with `npx remotion compositions`. Options: https://www.remotion.dev/docs/cli/render.md

## Input props

```
npx remotion render [composition-id] out/video.mp4 --props='{"title": "Hello"}'
npx remotion render [composition-id] out/video.mp4 --props=./props.json
```

Props shallow-merge over the composition's defaultProps.

## License key

Companies that need a Remotion license pass it to every render with `--license-key=...`; users who qualify for the free license pass `free-license`. Only pass it if a key is available. Add `--is-production=false` for test renders.

## Stills and frames

```
npx remotion still
npx remotion render [composition-id] out/frames --frames=0,30,90 --image-format=png
```

Frames are written as `element-[frame].[ext]`, zero-padded to the highest frame's digits. List the folder rather than guessing names, or pass `--image-sequence-pattern`.

## Transparent videos and timeline export

For transparency, see transparent-videos.md. For an editable timeline for DaVinci Resolve or Premiere, follow opentimeline.md; use it only when a timeline export is requested.