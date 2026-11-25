"""Build the Kiriyama townsfolk as toon .blends from the CC0 VRoid samples, with the same materials/outlines as toon Sam
(functions taken from ../../toon_sam/build_sam.py). Needs Blender 5.0.1 + the VRM add-on (as for build_sam.py).
Run:  blender -b -P build_cast.py -- [name ...]      names: grandma kid_girl kid_boy shopkeeper (default: all)
Writes ../cast/<name>.blend (armature <Name>_Rig, objects prefixed <Name>_) and ../cast/<name>_preview.png"""
import bpy, bmesh, math, sys, os, ast, addon_utils
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
VRM_DIR = os.path.join(HERE, '..', 'vrm'); OUTD = os.path.join(HERE, '..', 'cast'); os.makedirs(OUTD, exist_ok=True)
SAM = os.path.join(HERE, '..', '..', 'toon_sam', 'build_sam.py')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []

# ---- reuse Sam's helper functions + palette (everything before the module code that touches Sam's meshes)
_src = open(SAM, encoding='utf-8').read(); _keep = []
for n in ast.parse(_src).body:
    seg = ast.get_source_segment(_src, n)
    if isinstance(n, ast.FunctionDef): _keep.append(seg)
    elif isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ('LINE', 'C', 'DARK_RAMP', 'IRIS_RAMP', '_orig_toon'):
        _keep.append(seg)
code = '\n\n'.join(_keep).replace("'Sam_", "P + '_")
# the patched toon_mat (flat mode) must wrap the original: rename the first def
code = code.replace('def toon_mat(name, color=None, shadow=None, tex=None, tex_mode=\'color\', ramp=None', 'def _toon_base(name, color=None, shadow=None, tex=None, tex_mode=\'color\', ramp=None', 1)
code = code.replace('_orig_toon = toon_mat', '_orig_toon = _toon_base').replace('_orig_toon(', '_toon_base(')

KIDS = {'J_Bip_L_UpperLeg': (0.84, 0.74, 0.84), 'J_Bip_R_UpperLeg': (0.84, 0.74, 0.84), 'J_Bip_C_Spine': (0.94, 0.86, 0.94),
        'J_Bip_L_UpperArm': (0.90, 0.86, 0.90), 'J_Bip_R_UpperArm': (0.90, 0.86, 0.90)}
CAST = {
    # name: vrm, height (m), head scale, colours (None = keep the VRoid texture), notes
    'grandma': dict(vrm='Base_Female.vrm', h=1.46, head=1.0, bones={'J_Bip_C_Spine': (1.12, 1.0, 1.10)}, extras=('long_skirt', 'apron', 'bun'), hair=('#bdb7bd', '#8c8592', '#e4dfe4'), tops=('#8a6f7a', '#5d4752'), bottoms=('#4b3f45', '#30282d'), skin_sh='#d9aaa3'),
    'kid_girl': dict(vrm='AvatarSample_D.vrm', h=1.28, head=1.0, bones=KIDS, extras=('randoseru_red',), hair=('#26232c', '#141218', '#4a4656'), tops=None, bottoms=None, skin_sh=None),
    'kid_boy': dict(vrm='HairSample_Male.vrm', h=1.32, head=1.0, bones=KIDS, extras=('randoseru_black', 'yellow_cap'), hair=None, tops=None, bottoms=None, skin_sh=None),
    'shopkeeper': dict(vrm='Base_Male.vrm', h=1.70, head=1.0, bones={'J_Bip_C_Spine': (1.16, 1.0, 1.18), 'J_Bip_C_Chest': (1.04, 1.0, 1.04)}, extras=('maekake', 'hachimaki'), hair=('#2b2a30', '#18171c', '#4a4852'), tops=('#56617a', '#363e52'), bottoms=('#3a3a40', '#232328'), skin_sh='#d6a596'),
}


def build(name, cfg):
    global P, C
    P = name.capitalize()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if not any('vrm' in m for m in bpy.context.preferences.addons.keys()):
        addon_utils.enable('bl_ext.user_default.vrm', default_set=True)
    exec(code, globals())
    C['skin_sh'] = hexc(cfg['skin_sh']) if cfg['skin_sh'] else C['skin_sh']
    assert bpy.ops.import_scene.vrm(filepath=os.path.join(VRM_DIR, cfg['vrm'])) == {'FINISHED'}
    sc = bpy.context.scene
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]; arm.name = P + '_Rig'
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in meshes:
        for md in [m for m in o.modifiers if m.type == 'NODES']: o.modifiers.remove(md)
    for o in [o for o in bpy.data.objects if o.type == 'EMPTY']: o.hide_render = True; o.hide_viewport = True
    # materials: VRoid textures kept where cfg is None, flat Kiriyama palette otherwise
    for key, slot in (('hair', ('hair', 'hair_sh', 'hair_hi')), ('tops', ('hood', 'hood_sh')), ('bottoms', ('jean', 'jean_sh'))):
        if cfg[key]:
            for k, hx in zip(slot, cfg[key]): C[k] = hexc(hx)
    keep = {k for k in ('hair', 'tops', 'bottoms') if cfg[k] is None}
    for o in meshes:
        hulls = []
        for i, m in enumerate(o.data.materials):
            if m is None: hulls.append(None); continue
            n = m.name; tex = tex_of(m); a, ds = vrm_alpha(m)
            if 'HAIR' in n:
                nm = toon_mat(P + '_Hair_%d' % i, C['hair'], C['hair_sh'], tex=tex, tex_mode='color' if 'hair' in keep else 'flat', alpha=a or 'clip', highlight=C['hair_hi'])
                hulls.append(hull_mat(P + '_Line_Hair_%d' % i, tex))
            elif 'Tops' in n or 'Accessory' in n or 'Onepiece' in n:
                nm = toon_mat(P + '_Tops_%d' % i, C['hood'], C['hood_sh'], tex=tex, tex_mode='color' if 'tops' in keep else 'flat', alpha='clip')
                hulls.append(hull_mat(P + '_Line_Tops_%d' % i, tex))
            elif 'Bottoms' in n:
                nm = toon_mat(P + '_Bottoms_%d' % i, C['jean'], C['jean_sh'], tex=tex, tex_mode='color' if 'bottoms' in keep else 'flat', alpha='clip')
                hulls.append(hull_mat(P + '_Line_Bottoms_%d' % i, tex))
            elif 'Shoes' in n:
                nm = toon_mat(P + '_Shoes_%d' % i, tex=tex, alpha='clip'); hulls.append(hull_mat(P + '_Line_Shoes_%d' % i, tex))
            elif 'SKIN' in n:
                nm = toon_mat(P + '_Skin_%d' % i, tex=tex, shadow=C['skin_sh'], alpha=a); hulls.append(hull_mat(P + '_Line_Skin_%d' % i, tex if a else None))
            elif 'EyeIris' in n:
                nm = toon_mat(P + '_Iris_%d' % i, tex=tex, tex_mode='remap', ramp=IRIS_RAMP, lit_only=True, alpha=a); hulls.append(None)
            elif any(k in n for k in ('FaceBrow', 'FaceEyelash', 'FaceEyeline')):
                nm = toon_mat(P + '_FaceLine_%d' % i, tex=tex, tex_mode='remap', ramp=DARK_RAMP, lit_only=True, alpha=a); hulls.append(None)
            else:
                nm = toon_mat(P + '_FaceMisc_%d' % i, tex=tex, lit_only=True, alpha=a); hulls.append(None)
            nm.use_backface_culling = not ds
            o.data.materials[i] = nm
        if not o.name.startswith('Face'):
            add_outline(o, hulls, 0.0028 if 'Hair' not in o.name else 0.0022)
        o.name = P + '_' + o.name
    # face outline (skin faces only, reversed shell), as for Sam
    face = next((o for o in meshes if o.name.startswith(P + '_Face')), None)
    if face:
        fl = face.copy(); fl.data = face.data.copy(); fl.name = P + '_Face_Outline'; sc.collection.objects.link(fl)
        sk = [i for i, m in enumerate(face.data.materials) if m and 'Skin' in m.name]
        if sk:
            delete_faces(fl, lambda f: f.material_index != sk[0])
            fl.data.materials.clear(); fl.data.materials.append(hull_mat(P + '_Line_Face'))
            for p_ in fl.data.polygons: p_.material_index = 0
            bm = bmesh.new(); bm.from_mesh(fl.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(fl.data); bm.free()
            d = fl.modifiers.new('OutlineShell', 'DISPLACE'); d.direction = 'NORMAL'; d.mid_level = 0; d.strength = -0.0016
    # proportions (bone scales: kids = shorter legs/torso/arms so the head reads big), then height from the posed meshes
    arm.data.pose_position = 'POSE'
    for bn, s3 in cfg.get('bones', {}).items():
        arm.pose.bones[bn].scale = s3
    kid = cfg.get('bones') is KIDS
    if kid:                                            # the head bone inherits the spine scale: give it back and a bit more
        arm.pose.bones['J_Bip_C_Neck'].scale = (1 / 0.94 * 1.20, 1 / 0.86 * 1.18, 1 / 0.94 * 1.20)
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    def zrange():
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); zs = []
        for o in meshes:
            ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
            zs += [(mw @ v.co).z for v in me.vertices]; ev.to_mesh_clear()
        return min(zs), max(zs)
    z0, z1 = zrange(); s = cfg['h'] / (z1 - z0); arm.scale = (s, s, s)
    bpy.context.view_layer.update()
    body_o = next(o for o in meshes if o.name.startswith(P + '_Body'))
    hair_o = next((o for o in meshes if 'Hair' in o.name), None) or next((o for o in meshes if o.name.startswith(P + '_Face') and 'Outline' not in o.name), None)
    XLIM = 0.19                                        # torso only: T-pose arms must not widen the bands
    def band(o, za, zb):
        dg = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
        ps = [mw @ v.co for v in me.vertices]; ev.to_mesh_clear()
        ps = [p for p in ps if za <= p.z <= zb and abs(p.x) < XLIM] or ps
        return (min(p.x for p in ps), max(p.x for p in ps), min(p.y for p in ps), max(p.y for p in ps))
    def bonez(n): return (arm.matrix_world @ arm.pose.bones[n].head).z
    def attach(ob, bone):
        mw = ob.matrix_world.copy(); ob.parent = arm; ob.parent_type = 'BONE'; ob.parent_bone = bone
        bpy.context.view_layer.update(); ob.matrix_world = mw
    def piece(nm, bm, col, sh, bone, thick=0.0026):
        me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free()
        for p_ in me.polygons: p_.use_smooth = True
        ob = bpy.data.objects.new(P + '_' + nm, me); sc.collection.objects.link(ob)
        me.materials.append(toon_mat(P + '_' + nm, hexc(col), hexc(sh))); add_outline(ob, [hull_mat(P + '_Line_' + nm)], thick)
        attach(ob, bone); return ob
    def ring_tube(pts_rings):
        bm = bmesh.new(); R = [[bm.verts.new(p) for p in r] for r in pts_rings]
        for A, B_ in zip(R, R[1:]):
            n_ = len(A)
            for k in range(n_): bm.faces.new((A[k], A[(k + 1) % n_], B_[(k + 1) % n_], B_[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm
    ex = cfg.get('extras', ())
    zh = bonez('J_Bip_C_Hips'); zc = bonez('J_Bip_C_UpperChest'); zn = bonez('J_Bip_C_Neck'); zhd = bonez('J_Bip_C_Head')
    if 'long_skirt' in ex:                             # an older woman's mid-calf skirt over the school skirt + socks
        bi = [i for i, m in enumerate(body_o.data.materials) if m and 'Bottoms' in m.name]
        if bi: delete_faces(body_o, lambda f: f.material_index in bi)
        x0, x1, y0, y1 = band(body_o, zh - 0.02, zh + 0.10); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rings = []
        for j in range(9):
            u = j / 8; z = zh + 0.10 - u * (zh + 0.10 - 0.20); fl = 1.06 + 0.38 * u ** 0.8
            rings.append([Vector((cx + math.cos(a) * (x1 - x0) / 2 * fl * (1 + 0.025 * math.sin(a * 7 + j)), cy + math.sin(a) * (y1 - y0) / 2 * fl * 1.08, z))
                          for a in [2 * math.pi * k / 40 for k in range(40)]])
        piece('long_skirt', ring_tube(rings), '#5b4b52', '#3a2f35', 'J_Bip_C_Hips')
    if 'apron' in ex or 'maekake' in ex:               # apron: bib + skirt panel (grandma), waist-to-knee maekake (shopkeeper)
        top = zc + 0.02 if 'apron' in ex else zh + 0.06
        bot = 0.42 if 'apron' in ex else 0.50
        rows = []; yhang = None
        x0, x1, _, _ = band(body_o, zh - 0.03, zh + 0.03); cxw = (x0 + x1) / 2; ww = (x1 - x0)
        for j in range(14):                            # fixed widths (no band jitter): narrow bib with soft top corners,
            u = j / 13; z = top - u * (top - bot)       # flaring to a skirt panel; below the bust it hangs straight
            _, _, y0, _ = band(body_o, z - 0.03, z + 0.03)
            if 'long_skirt' in ex and z < zh + 0.10: y0 -= 0.05 + 0.12 * (zh + 0.10 - z)
            if z < zc - 0.06: yhang = y0 if yhang is None else min(yhang, y0 + 0.004 * (z > zh - 0.02))
            yy = yhang if yhang is not None and z < zc - 0.06 else y0
            t = min(1, max(0, (zh + 0.12 - z) / 0.16)); t = t * t * (3 - 2 * t)
            w = (ww * (0.30 + 0.50 * t) if 'apron' in ex else ww * 0.50)
            if j == 0: w *= 0.86
            rows.append([Vector((cxw + w * (2 * i / 8 - 1), yy - 0.014 - 0.012 * (1 - (2 * i / 8 - 1) ** 2), z)) for i in range(9)])
        bm = bmesh.new(); R = [[bm.verts.new(p) for p in r] for r in rows]
        for A, B_ in zip(R, R[1:]):
            for k in range(8): bm.faces.new((A[k], A[k + 1], B_[k + 1], B_[k]))
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.006)
        col = ('#d8cdb4', '#a99c86') if 'apron' in ex else ('#22345c', '#141f38')
        piece('apron', bm, col[0], col[1], 'J_Bip_C_Spine' if 'apron' in ex else 'J_Bip_C_Hips')
    if 'bun' in ex and hair_o:
        x0, x1, y0, y1 = band(hair_o, zhd + 0.05, zhd + 0.20)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
        bmesh.ops.scale(bm, vec=(0.050, 0.042, 0.045), verts=bm.verts)
        bmesh.ops.translate(bm, vec=((x0 + x1) / 2, y1 + 0.012, zhd + 0.14), verts=bm.verts)
        piece('bun', bm, cfg['hair'][0], cfg['hair'][1], 'J_Bip_C_Head', 0.0018)
    if 'hachimaki' in ex and hair_o:
        x0, x1, y0, y1 = band(hair_o, zhd + 0.08, zhd + 0.12); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rings = [[Vector((cx + math.cos(a) * ((x1 - x0) / 2 + 0.010 + dr), cy + math.sin(a) * ((y1 - y0) / 2 + 0.010 + dr), zhd + 0.10 + dz)) for a in [2 * math.pi * k / 36 for k in range(36)]]
                 for dz, dr in ((-0.02, 0.004), (0.0, 0.012), (0.02, 0.004))]
        piece('hachimaki', ring_tube(rings), '#eae6dc', '#b9b2a6', 'J_Bip_C_Head', 0.0016)
    if 'yellow_cap' in ex and hair_o:
        x0, x1, y0, y1 = band(hair_o, zhd + 0.06, zhd + 0.30); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context='VERTS')
        bmesh.ops.scale(bm, vec=((x1 - x0) / 2 * 1.04, (y1 - y0) / 2 * 1.04, 0.10), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(cx, cy, zhd + 0.13), verts=bm.verts)
        vs = [bm.verts.new(Vector((cx + math.cos(a) * 0.075, y0 - 0.03 - math.sin(a) * 0.06 * 0 + 0.0, zhd + 0.125)) ) for a in []]
        piece('yellow_cap', bm, '#f2c623', '#b88c12', 'J_Bip_C_Head', 0.0018)
    for col_key in ('randoseru_red', 'randoseru_black'):
        if col_key in ex:
            x0, x1, y0, y1 = band(body_o, zc - 0.20, zc + 0.02); cx = (x0 + x1) / 2
            w, hgt, d = 0.23, 0.29, 0.16; zt = zc + 0.05; yb = y1 + 0.005
            bm = bmesh.new(); r_ = bmesh.ops.create_cube(bm, size=1)['verts']
            bmesh.ops.scale(bm, vec=(w, d, hgt), verts=r_); bmesh.ops.translate(bm, vec=(cx, yb + d / 2, zt - hgt / 2), verts=r_)
            bmesh.ops.bevel(bm, geom=[e for e in bm.edges], offset=0.03, segments=3, affect='EDGES')
            for side in (-1, 1):                       # shoulder straps
                pts = [Vector((cx + side * 0.07, yb + 0.01, zt - 0.02)), Vector((cx + side * 0.075, (y0 + y1) / 2, zn + 0.0)),
                       Vector((cx + side * 0.085, y0 - 0.008, zc - 0.02)), Vector((cx + side * 0.11, (y0 + y1) / 2, zc - 0.17)),
                       Vector((cx + side * 0.09, yb + 0.01, zt - hgt + 0.03))]
                ring = None
                for i_, p in enumerate(pts):
                    q = [bm.verts.new(p + Vector((dx, 0, dz))) for dx, dz in ((-0.016, -0.003), (0.016, -0.003), (0.016, 0.003), (-0.016, 0.003))]
                    if ring:
                        for k in range(4): bm.faces.new((ring[k], ring[(k + 1) % 4], q[(k + 1) % 4], q[k]))
                    ring = q
            c = ('#b8202a', '#741219') if col_key.endswith('red') else ('#1d1b22', '#0d0c10')
            piece('randoseru', bm, c[0], c[1], 'J_Bip_C_UpperChest')
    # preview (front, toon) so the cast can be checked
    sun = bpy.data.objects.new('Key', bpy.data.lights.new('Key', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.0; sun.data.color = (1.0, 0.82, 0.62); sun.rotation_euler = Vector((-0.42, -0.84, 0.30)).to_track_quat('Z', 'Y').to_euler()
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 2.0
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0, -4, 0.95); cam.rotation_euler = (math.radians(90), 0, 0)
    sc.render.engine = 'BLENDER_EEVEE'; sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x, sc.render.resolution_y = 512, 1024
    sc.render.filepath = os.path.join(OUTD, name + '_preview.png'); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam); bpy.data.objects.remove(sun)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTD, name + '.blend'))
    print('SAVED', name, 'scale', round(s, 3), 'height', cfg['h'])


for nm in (ARGS or list(CAST)):
    build(nm, CAST[nm])
