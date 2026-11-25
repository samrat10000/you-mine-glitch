# VRoid CC0 cast pool (for shot 05 and later)

Source: https://opengameart.org/content/vroid-studio-cc0-models. Author "VRoid Project", submitted by hecko. The page licence is **CC0** for every file. Hecko has no other VRoid uploads.
Each .vrm also embeds its own licence metadata:
- "CC0": licence_name is CC0.
- "VRoid Hub (Other)": licence_name is Other, linking the VRoid Hub licence with everyone allowed, commercial use allowed, modification allowed, redistribution allowed, credit unnecessary. Same terms as Sakurada Fumiriya, see ../toon_sam/SOURCES.md.

Heights are the bounding box of the A/T-pose model, including hair, ears and shoes. Front renders are in `renders/`, all of them together in `cast_sheet.png`. None of these is an elderly person, a child or a middle-aged man. All are young-adult / teen VRoid samples, so age, scale and costume changes are needed in Blender.

| File | Name (meta) | Look: gender / age | Hair | Outfit | Height | Licence (page / VRM meta) | Possible use |
|---|---|---|---|---|---|---|---|
| vrm/AvatarSample_D.vrm | 千駄ヶ谷渋 | female, teen | black bob, side clip | school uniform: navy vest, white shirt, red bow, pleated skirt, knee socks | 1.616 m | CC0 / VRoid Hub (Other) | a kid (scaled), townsperson |
| vrm/AvatarSample_D_Darkness.vrm | AvatarSample_D | female, young adult, elf ears | silver-white, long | black gothic long coat | 1.733 m | CC0 / CC0 | not a fit for Kiriyama |
| vrm/AvatarSample_E.vrm | ビビ | female, youthful, small | brown bob | green apron dress, star hem, lace-up boots | 1.412 m | CC0 / VRoid Hub (Other) | **best base for a kid** (smallest), shop apron |
| vrm/AvatarSample_F.vrm | ヴィータ | female, young adult | white-cyan, horned headpiece | sci-fi bodysuit | 1.713 m | CC0 / VRoid Hub (Other) | not a fit |
| vrm/AvatarSample_G.vrm | ヴィクトリア・ルービン | female, young adult | blonde, long side tail | pink idol dress | 1.737 m | CC0 / VRoid Hub (Other) | not a fit |
| vrm/Base_Female.vrm | Base_Female | female, teen | teal short (placeholder) | school uniform (vest, bow, skirt) | 1.598 m | CC0 / CC0 | **Grandma base** (plain body, re-dress: grey hair, apron, hunch) |
| vrm/Base_Male.vrm | Base_Male | male, teen | teal short, no fringe | school uniform (vest, tie, trousers) | 1.757 m | CC0 / CC0 | **Shopkeeper base** (plain body: apron, headband, heavier build) |
| vrm/HairSample_Female.vrm | HairSample_Female | female, teen | black twin tails, cat ears | white dress, white sneakers | 1.668 m | CC0 / CC0 | a kid (scaled, ears removed) |
| vrm/HairSample_Male.vrm | HairSample_Male | male, teen | black, messy fringe | white hoodie, black trousers | 1.806 m | CC0 / CC0 | **a kid (boy)** scaled; also a Mirror-Sam test |
| vrm/Sakurada Fumiriya.vrm | 桜田 史利矢 | male, teen | orange-brown, tidy | school uniform (vest, tie) | 1.909 m | CC0 / VRoid Hub (Other) | Sam's base (already used) |
| vrm/Sendagaya Shino.vrm | 千駄ヶ谷篠 | female, teen | long black, straight | school uniform (vest, ribbon, skirt) | 1.645 m | CC0 / VRoid Hub (Other) | Mom / Mirror-Mom base (aged up, re-dressed) |

All 11 VRMs are under 50 MB (14.2 to 21.0 MB), so none were skipped. Render script: `scripts/cast_render.py` (Blender 5.0.1 + VRM add-on v4.10.5, EEVEE, orthographic front view, 512x1024).
