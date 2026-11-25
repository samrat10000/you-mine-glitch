# PLAYBOOK: 5 O'CLOCK Ep1 "The Fourth Note" (63 s, 18 shots), fully planned

The worked example of the planning depth this skill requires. Shots 01-04 are built (code in
`reference/5oclock_ep1v3/`); 05-18 are written exactly as they are to be built. For a new episode, write
the same table for every shot BEFORE building.

**Logline.** Every town in Japan plays a song at five o'clock. Kiriyama's has four notes. Today it stops
after three, and Sam, the only one wearing headphones, is the only one who notices which side of the mirror he's on.

**Cast.** Sam 17 (lean, narrow shoulders, long-ish hair, over-ear headphones, oversized grey hoodie with
uneven strings, red glasses, konbini bag). Mirror-Sam (hair parted the other way, strings swapped, pupils
never catch light, moves half a beat early). Grandma Hoshino (tiny, bent, sharp eyes, bamboo broom, kappogi
apron). Shopkeeper (maekake apron, hachimaki). Two kids (randoseru, yellow cap). The Listener (kaiju: head =
hundreds of rusted Showa loudspeaker horns turning together like sunflowers; too-many-jointed arms).
**World.** Mountain valley town on the sea, one train line, rice fields, orange curve mirrors, bosai musen
speakers on poles, the 1964 radio tower with a blinking red light, vending machine, railway crossing.
**Accent colour:** red only (glasses, mirror poles, tower light).

## Shot table
| # | name | s | camera | what moves | wow | how it is built | line(s) | cut out |
|---|---|---|---|---|---|---|---|---|
| 01 | The speaker | 0-3 | ECU locked, push 2% | crow lands on the rusted horn, horn wobbles, ruffle, dust in beam, static click | landing weight: claws grip, 2-beat wing fold | CC0 raven GLB clips slerp-blended, toes locked; lathe horn; painted sky (LOCKED v4) | N: "Every town in Japan plays a song at five o'clock. Ours has four notes." (0.4 s) | shape match: round horn -> round mirror |
| 02 | The mirror | 3-6 | medium on a curve mirror, slight push | golden 4:59 street; inside the mirror it is night with a figure; a maple leaf blows across, inside it blows the other way | 3 s hook | mirror glass = UV emission pass; painted night insert with convex warp; real maple outline | (N continues) | cut on leaf exit |
| 03 | Kiriyama | 6-9.5 | wide, slow crane down, 6 parallax layers | sun sinking, clouds drift, 2-car train, crossing bars lower, laundry sways, tower blinks | mountain shadow creeps across the fields | town in a local frame, garment builder, kawara tiles, invisible occluder for the shadow | N: "It has played every day since 1964. Nobody ever asked why." (6.3 s) | train direction continues into 04 |
| 04 | Sam rides home | 9.5-13.5 | side-on tracking at hub height, lens 32, he overtakes | coasting downhill, mouthing lyrics, bag swings, hair/strings whip, spokes blur, wire shadows flick, passes the Yamada shop window | his reflection is 12 frames late (hidden detail) | Sam VRM toon rig with wrap-grip IK on a photo-matched mamachari; road detail; holdout glass + mirror camera + late twin | (music only) | he exits frame right; 05a opens on the shop pier |
| 05 | The ritual | 13.5-17 | 3 cuts on the beat, 28 frames each | (a) Grandma stops sweeping, turns her shop's little mirror to face the wall (profile, lens 45). (b) Two kids stop running, press hands over their ears, look up (backlit, sea and sun, pole clock 4:59, camera looking +Y). (c) Shopkeeper (back to camera) pulls the shutter down at the Yamada shop, glances over his shoulder | all three move in sync without seeing each other; the same clock in each | reuse 04's street via ast-exec (signs swapped: 星野商店), cast blends with IK hands on broom/shutter, run cycle with stride matched to speed, on twos | Grandma: "Ears. Quickly." (14.2 s, sharp whisper) | all three glance at the clock -> insert |
| 06 | 4:59 | 17-19 | insert over Sam's shoulder onto the phone on the handlebar, shallow DOF | clock flips 16:59 -> 17:00, battery 3%, thumb skips a song | the flip lands on the first chime note of 07 | phone = emission screen texture per frame; thumb from Sam's hand rig (real grip on the phone mount) | - | sound match: flip = note 1 |
| 07 | Three notes | 19-23.5 | low angle up at the speaker pole, huge sunset sky | note 1: a hundred crows lift off the wires in a wave; note 2: the wave rolls across town; note 3: rings ripple through the clouds; the 4th never comes, the horn vibrates in silence | you SEE the sound: each ring = one note | crow GLB instanced with offset clips along the wires; ring displacement in the painted clouds; horn vibration 2-frame shake | - | silence carries into 08 |
| 08 | The frozen town | 23.5-28.5 | one continuous fly-through at walking height, weaving | everything stops mid-motion: leaves hang, kid mid-jump, watering-can droplets, crow mid-flap, vending steam; ends on Sam still riding | the signature shot (build first as a 2 s test) | all objects posed once and held; camera spline on ones with handheld drift; DOF pulls on passing faces | - | lands on Sam -> 09 CU |
| 09 | Silence | 28.5-31.5 | CU on Sam, he brakes into a medium | music cuts: battery 0%; he pulls headphones down to his neck; only the chain ticking as he coasts; looks around, frowns | the quietest moment of the reel | headphone constraint switch head->neck; brake squeeze in the hand rig; foot comes down and LOCKS to the road | Sam: "...Hello?" (29.8 s) | eyeline to Grandma |
| 10 | Grandma's eyes | 31.5-35 | Sam walks the bike past her; slow push on her face | body perfectly still, only her eyes slide to follow him; lips don't move when she speaks | only the eyes move, a few pixels | eye bones only animated (on ones for smoothness); everything else frozen | Grandma: "Don't look at the mirror, Sam." (32.4 s, no lip movement) | he looks at the mirror -> OTS |
| 11 | In the mirror | 35-38.5 | over Sam's shoulder into the curve mirror, slow push | inside: night, the whole town standing in the street facing him; behind them the sky over the mountains cracked like glass with something huge behind it | fisheye crowd | mirror UV pass + rendered night town (second scene, night look) with convex warp | - | whip pan |
| 12 | Closer | 38.5-42 | whip pan to the real street, whip back to the mirror | real street: sunset, frozen people, nobody looking; back to the mirror: the crowd is much closer, filling the glass | horror beat on whip pans with smear frames | 2-3 directional-blur smear frames each way | - | push in on the mirror |
| 13 | Mirror-Sam | 42-45 | CU of the mirror, Sam's face in it | Sam turns his head; his reflection doesn't, keeps looking, smiles slowly, finger to lips | two of the same character, half a beat apart | mirror-Sam = Sam rig duplicated, mirrored hair part/strings, pupils without highlight, animated 6 frames early | Sam: "That's not me." (43.0 s); Mirror-Sam: "Your turn." (44.4 s) | ECU mouth |
| 14 | The fourth note | 45-48.5 | ECU on mirror-Sam's mouth, hard cut wide | he breathes in and hums the 4th note; every speaker plays it from inside the mirrors; every curve mirror cracks outward in a ring at once | hand-timed crack frames with glints | crack = animated voronoi mask on the glass UV, 6 hand-keyed growth frames, glint sprites | - | hard cut to the scale shot |
| 15 | The Listener | 48.5-53 | huge wide from Sam's eye level, slow tilt up | the sky splits along the horizon, clouds pour toward the crack, a hand the size of the mountain presses through, a head of rusted horns rises, all turn toward Kiriyama at once; the tower light bends toward the crack | the kaiju reveal (build second as a test) | horns = instanced lathe horns with per-horn delay turning (sunflower follow); arm from a real rigged creature/human base, extra joints; painted sky warp; atmospheric haze for scale | N: "The fourth note was never ours to play." (49.0 s) | cut to POV |
| 16 | Welcome home | 53-56 | Sam's POV down the street | the town unfreezes: leaves fall, kid lands, water splashes; every shop sign is now written backwards; everyone turns to Sam and smiles together | one frame flips the world: mirrored signs, Grandma's hair part flipped | text objects scale -1 on X at the unfreeze frame; synchronized head turns on twos | Town in unison: "Okaeri, Sam." (54.0 s) | he backs away |
| 17 | The wrong side | 56-59 | Sam backs into a curve mirror; close two-shot | in the glass: the real Kiriyama, warm sunset; his mother on their doorstep calling him, she can't see him; he presses his hand to the mirror | the twist: he's been on the other side since 5:00 | mirror insert = day render of the house; hand contact with the glass (palm flat, fingers spread, no gap) | Sam: "Mom...?" (57.2 s, breaking) | cut to insert |
| 18 | Rule seven | 59-63 | top-down insert on an old police notebook, then black | Officer Tanaka's rules notebook, rule 7 torn out; under the tear new ink writes itself in Sam's handwriting; black; the chime plays 3 notes, then nothing | the Ep2 hook | paper texture + ink write-on mask along a stroke path; torn edge real fibre outline | N: "Rule seven. Never finish the song." (59.5 s) | end card on black |

## Sound plan
Score: piano-led (SOUND_VOICE), opens solo at 0.9 s, thins under each line, total drop at 09, swells for
15, final ringing chord under 18's black. SFX per shot from the table above. Chime = 4-tone
pin-pon-pan-pon through a loudspeaker model with mountain echo; only 3 notes until 14.

## Status at handover (2026-11-23)
01 v4 LOCKED; 02 v1 passed; 03 v2 sent ("perfect, but" notes applied); 04 v4 sent (handlebar fix);
cast for 05 built (grandma, kid_girl, kid_boy, shopkeeper). Next: 05 The ritual.
