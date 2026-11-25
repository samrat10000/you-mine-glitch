---
name: "glb-vehicle-builder"
description: "Build a stylized vehicle (car, bike, mech) as a GLB plus a preview render, with marker-ink outlines, using Blender bpy. Use when Sam asks for a 3D model or GLB."
---

# GLB vehicle builder

Deliverable: one `.glb` per model plus a 1080x1350 preview PNG (reel-friendly), sent with SendUserFile.

## Ground rules
- Only build faithful copies of designs the user owns. For another artist's art (signed images, famous designs), build an original in the same general mood and say so before starting.
- Default style, every build: black marker ink outlines baked into the GLB; long body proportions with wheels well apart; curvy/hourglass shaping; chunky wide tires that stick out past their fenders.

## Setup
- `pip install --break-system-packages bpy` (Blender as a Python module). Render with Cycles CPU, denoise on.
- Colour management: `view_transform = 'Standard'` (AgX washes sampled colours out). Convert sRGB hex to linear before setting Base Color.

## Workflow
1. Sample the palette first (PIL quantize + point samples) and name every material after its role (Paint_Amber, Rubber, Chrome...).
2. List every part and sub-part. Each gets its own named object, grouped under empties (Body, Wheels, Engine, Lights, Livery, Details).
3. Build hard-surface panels as extruded profile slabs (top-down for cars, side-profile for bikes) with an inset chamfer plus a 3-segment angle-limited bevel. Then mark edges sharp above 35 degrees and shade smooth.
   - Use curvy (Catmull-Rom) outlines only for tanks, seats and organic panels. Armor reads better as angular plates, because pillowy shapes look toy-like.
4. Wheel arches: boolean-subtract a wheel cutter whose depth is only the wheel width plus about 8 cm. Long cutters slice the neighbouring bodywork.
5. Wheels: spun tire profile, chevron tread blocks, an uncapped rim barrel (capped barrels hide the spokes), spokes, lip ring, brake disc, caliper, hub and lug bolts.
6. Decals and graffiti: flat meshes or ribbons projected onto the body with a Shrinkwrap PROJECT modifier against a joined target mesh. Delete vertices that miss, because they cause giant spikes. Keep seams and strokes off steep drops between parts.
7. Weathering: ragged blobs (high jag) layered as faded, rust and core, plus drips and scratches. Even round spots read as polka dots.
8. Ink (do this last):
   - Crease lines: thin 5-sided tubes on edges above about 38 degrees, taken from the un-bevelled mesh. Add slight random overshoot so they read as marker strokes.
   - Silhouette: an inverted hull (vertices pushed along their normals, faces flipped) with a black material that uses backface culling.
   - Skip ink on tiny or flat parts.
9. Export the car collection only, with `export_apply=True`. Re-import the GLB to verify the part count, triangle count and size.

## Upgrading a GLB the user supplies
- Copy the upload first. Never name a helper script `inspect.py`, because it shadows the stdlib module and crashes bpy. Write the import logs to a file; they are huge.
- Render 4 overview angles plus close-ups (cabin with roof and glass hidden, front, rear) before changing anything. Ray-cast down through problem areas to find which object is really at fault.
- Imported glTF meshes are split triangle soup. Weld them (remove_doubles 1e-4) and recalculate normals before any boolean, or the cut silently does nothing.
- Weld a copy before extracting crease lines too. Otherwise every edge counts as a border and the file grows by millions of triangles. Skip lines on edges under 6 mm and on dense tires and treads, and skip hulls on flat lettering and decals.
- To move a wheel outward, shift the whole wheel-assembly empty and add a spacer plus studs, so nothing floats.
- Glowing lights: raise the emission strength (about 8-16) on the existing emitter materials and give plain lamp lenses an emissive material. Check the size of the final GLB; the result should stay within about 2x the original.

## Preview render
- In Cycles, give the hull material Backfacing mixed with Transparent, because Cycles ignores backface culling. Turn off shadow, diffuse, glossy and transmission ray visibility on hulls and ink, or they darken the whole model.
- Auto-frame the camera from the bounding box. Check for clipping at the frame edges before delivering.
- For the world, use a Light Path Is-Camera-Ray mix so the background is plain off-white while the lighting stays soft. Use a light tiled floor with scattered debris chips.
- Do a low-sample test render, compare it side by side with the reference, fix, then render the final at about 56-64 samples.

## Delivery
- Send the GLB and preview together, with a short note on the part count and any viewer caveats (hull outlines need a viewer that culls back faces).