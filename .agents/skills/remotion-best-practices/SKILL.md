---
name: "remotion-best-practices"
description: "Router for Remotion work: creating videos and projects, markup, captions, Studio preview, rendering and docs. Use whenever building or editing a Remotion video."
---

(Source: remotion-dev/skills v4.0.545. This is the router page. The reference pages it links to (remotion-create, remotion-markup, remotion-captions and the rest) ship in the remotion zip in project files; when they are missing, read the matching page at https://www.remotion.dev/docs instead.)

## Preserve user changes

Users may edit the code outside the conversation. If you see a surprising change, assume it was intentional or ask; do not overwrite it.

## Creating a video or new project

Load the remotion-create reference whenever the user asks to make a new video or composition, or no Remotion project exists yet.

## Topics

- Writing Remotion React markup, video matting or background removal: remotion-markup.
- Maps, routes, GeoJSON, 3D geographic flyovers: remotion-maps.
- Trimming, cropping, video metadata in the browser: remotion-multimedia.
- Editable-in-Studio markup: remotion-interactivity.
- Captions: remotion-captions.
- SaaS, Player, Lambda, Vercel, Cloudflare, Express rendering: remotion-saas.
- API lookups: remotion-docs. Licensing: remotion-license. Upgrades: remotion-upgrade.

## Open the preview

Once the project runs, open Studio so the user can preview and steer:

```bash
npx remotion studio            # opens the browser
npx remotion studio --no-open  # prints the URL for an in-app browser
```

Visit a composition at `/[composition-id]`, for example `http://localhost:3000/MapAnimation`.

## Render

Only render when the user is explicit ("render the video", "export", "give me the MP4"). The Studio render UI is often easier.

```
npx remotion render
```

See remotion-render for options.