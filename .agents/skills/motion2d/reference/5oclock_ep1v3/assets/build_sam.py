"""Build Sam (toon) from the CC0 VRoid sample 'Sakurada Fumiriya'. Saves toon3d/sam_toon.blend.
Run: blender -b -P build_sam.py
"""
import bpy, bmesh, math, addon_utils
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = 'C:/Users/cross/Downloads/xc/anime-5oclock/toon3d/'
VRM = ROOT + 'dl/base/sakurada_fumiriya/Sakurada Fumiriya.vrm'

def hexc(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, a)

LINE = hexc('#2a1c22')

# ---------------------------------------------------------------- import
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
if not any('vrm' in m for m in bpy.context.preferences.addons.keys()):
    addon_utils.enable('bl_ext.user_default.vrm', default_set=True)
assert bpy.ops.import_scene.vrm(filepath=VRM) == {'FINISHED'}
sc = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
arm.name = 'Sam_Rig'
body, face, hair = bpy.data.objects['Body'], bpy.data.objects['Face'], bpy.data.objects['Hair001']
hair.name = 'Hair'
print('arm world identity:', arm.matrix_world == Matrix.Identity(4))
for o in (body, face, hair):
    for md in [m for m in o.modifiers if m.type == 'NODES']: o.modifiers.remove(md)
for o in [o for o in bpy.data.objects if o.type == 'EMPTY']:
    o.hide_render = True; o.hide_viewport = True

# remove the tie (Accessory material faces)
def delete_faces(obj, pred):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = [f for f in bm.faces if pred(f)]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(obj.data); bm.free()
acc = [i for i, m in enumerate(body.data.materials) if 'Accessory' in m.name][0]
delete_faces(body, lambda f: f.material_index == acc)

# ---------------------------------------------------------------- helpers
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

def bvh_of(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in objs:
        ev = o.evaluated_get(dg); me = ev.to_mesh()
        off = len(verts); mw = o.matrix_world
        verts += [mw @ v.co for v in me.vertices]
        polys += [[off + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)

def cast_in(bvh, start, d):  # from far outside toward d, return first hit
    hit = bvh.ray_cast(Vector(start), Vector(d).normalized())
    return hit[0]

def link(obj, coll=None):
    (coll or sc.collection).objects.link(obj); return obj

def parent_bone(obj, bone):
    bpy.context.view_layer.update()
    mw = obj.matrix_world.copy()
    obj.parent = arm; obj.parent_type = 'BONE'; obj.parent_bone = bone
    bpy.context.view_layer.update(); obj.matrix_world = mw

def mesh_obj(name, bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(50))
    return link(bpy.data.objects.new(name, me))

def curve_obj(name, pts, bevel, cyclic=False, res=3, kind='POLY'):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = bevel; cu.bevel_resolution = res; cu.use_fill_caps = True
    sp = cu.splines.new(kind)
    if kind == 'BEZIER':
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        cu.resolution_u = 16
    else:
        sp.points.add(len(pts) - 1)
        for sp_p, p in zip(sp.points, pts): sp_p.co = (*p, 1)
    sp.use_cyclic_u = cyclic
    return link(bpy.data.objects.new(name, cu))

def torus_bm(R, r, seg=48, ring=16):
    bm = bmesh.new(); grid = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; row = []
        for j in range(ring):
            b = 2 * math.pi * j / ring
            row.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b))))
        grid.append(row)
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((grid[i][j], grid[(i + 1) % seg][j], grid[(i + 1) % seg][(j + 1) % ring], grid[i][(j + 1) % ring]))
    return bm

def cyl_bm(r, depth, seg=40):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if all(abs(v.co.z) > depth * 0.45 for v in e.verts)],
                    offset=min(r, depth) * 0.18, segments=3, affect='EDGES', clamp_overlap=True)
    return bm

# ---------------------------------------------------------------- landmarks (rest pose)
fb = bvh_of([face]); hb = bvh_of([hair]); bb = bvh_of([body]); hfb = bvh_of([hair, face])
fme = face.data
iris = [i for i, m in enumerate(fme.materials) if 'EyeIris' in m.name][0]
def centroid(sign):
    pts = [face.matrix_world @ fme.vertices[v].co for p in fme.polygons if p.material_index == iris for v in p.vertices]
    pts = [p for p in pts if p.x * sign > 0]
    return sum(pts, Vector()) / len(pts)
eyeL, eyeR = centroid(1), centroid(-1)  # L = +X (character's left)
ez = (eyeL.z + eyeR.z) / 2
face_front = min(cast_in(fb, (x, -1, ez), (0, 1, 0)).y for x in (eyeL.x, eyeR.x))
head_c = Vector((0, -0.003, ez + 0.01))
print('eyes', eyeL, eyeR, 'face front y', face_front)

# ---------------------------------------------------------------- materials
def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); m.surface_render_method = 'DITHERED'
    return m, nt

def toon_mat(name, color=None, shadow=None, tex=None, tex_mode='color', ramp=None, lit_only=False,
             alpha=None, highlight=None, rim=True, cull=False):
    """color/shadow: RGBA; tex: image; tex_mode 'color' | 'mul' | 'remap'(luminance->ramp);
    alpha: None | 'clip' | 'blend' (from texture alpha)."""
    m, nt = new_mat(name); N, L = nt.nodes, nt.links
    out = N.new('ShaderNodeOutputMaterial'); out.location = (1400, 0)
    base = None
    if tex is not None:
        t = N.new('ShaderNodeTexImage'); t.image = tex; t.location = (-900, 200)
        if tex_mode == 'remap':
            bw = N.new('ShaderNodeRGBToBW'); L.new(t.outputs[0], bw.inputs[0])
            cr = N.new('ShaderNodeValToRGB'); L.new(bw.outputs[0], cr.inputs[0])
            els = cr.color_ramp.elements
            for k, (pos, col) in enumerate(ramp):
                e = els[k] if k < 2 else els.new(pos); e.position = pos; e.color = col
            base = cr.outputs[0]
        elif tex_mode == 'mul':
            mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs[0].default_value = 1; L.new(t.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = color
            base = mx.outputs[2]
        else:
            base = t.outputs[0]
    else:
        rgb = N.new('ShaderNodeRGB'); rgb.outputs[0].default_value = color; base = rgb.outputs[0]
    col = base
    if not lit_only:
        diff = N.new('ShaderNodeBsdfDiffuse'); diff.location = (-600, -200)
        s2r = N.new('ShaderNodeShaderToRGB'); L.new(diff.outputs[0], s2r.inputs[0])
        bw = N.new('ShaderNodeRGBToBW'); L.new(s2r.outputs[0], bw.inputs[0])
        cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.interpolation = 'CONSTANT'
        cr.color_ramp.elements[1].position = 0.12; L.new(bw.outputs[0], cr.inputs[0])
        lit = cr.outputs[0]
        # shadow colour
        if shadow is None:
            sh = N.new('ShaderNodeMix'); sh.data_type = 'RGBA'; sh.blend_type = 'MULTIPLY'; sh.inputs[0].default_value = 1
            L.new(base, sh.inputs[6]); sh.inputs[7].default_value = hexc('#a5869c'); shc = sh.outputs[2]
        elif tex is not None:
            sh = N.new('ShaderNodeMix'); sh.data_type = 'RGBA'; sh.blend_type = 'MULTIPLY'; sh.inputs[0].default_value = 1
            L.new(base, sh.inputs[6]); sh.inputs[7].default_value = shadow; shc = sh.outputs[2]
        else:
            r2 = N.new('ShaderNodeRGB'); r2.outputs[0].default_value = shadow; shc = r2.outputs[0]
        # lit side warm tint (golden hour)
        warm = N.new('ShaderNodeMix'); warm.data_type = 'RGBA'; warm.blend_type = 'MULTIPLY'; warm.inputs[0].default_value = 1
        L.new(base, warm.inputs[6]); warm.inputs[7].default_value = hexc('#fff0e0')
        mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.location = (300, 0)
        L.new(lit, mix.inputs[0]); L.new(shc, mix.inputs[6]); L.new(warm.outputs[2], mix.inputs[7])
        col = mix.outputs[2]
        geo = N.new('ShaderNodeNewGeometry')
        if highlight is not None:  # anime 'angel ring' band on the hair, lit side only
            sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sep.inputs[0])
            band = N.new('ShaderNodeValToRGB'); band.color_ramp.interpolation = 'CONSTANT'
            e = band.color_ramp.elements; e[0].color = (0, 0, 0, 1); e[1].position = 0.50; e[1].color = (1, 1, 1, 1)
            e3 = e.new(0.66); e3.color = (0, 0, 0, 1)
            L.new(sep.outputs[2], band.inputs[0])
            lw = N.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.5
            fc = N.new('ShaderNodeMath'); fc.operation = 'LESS_THAN'; fc.inputs[1].default_value = 0.55
            L.new(lw.outputs['Facing'], fc.inputs[0])
            m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; L.new(band.outputs[0], m1.inputs[0]); L.new(fc.outputs[0], m1.inputs[1])
            m2 = N.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(lit, m2.inputs[1])
            hm = N.new('ShaderNodeMix'); hm.data_type = 'RGBA'; hm.location = (600, 0)
            L.new(m2.outputs[0], hm.inputs[0]); L.new(col, hm.inputs[6]); hm.inputs[7].default_value = highlight
            col = hm.outputs[2]
        if rim:  # thin soft warm rim from screen-right/back
            lw = N.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.5
            fr = N.new('ShaderNodeMath'); fr.operation = 'GREATER_THAN'; fr.inputs[1].default_value = 0.9
            L.new(lw.outputs['Facing'], fr.inputs[0])
            dirv = N.new('ShaderNodeCombineXYZ'); d = Vector((0.75, 0.6, 0.25)).normalized()
            for k in range(3): dirv.inputs[k].default_value = d[k]
            dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
            L.new(geo.outputs['Normal'], dot.inputs[0]); L.new(dirv.outputs[0], dot.inputs[1])
            side = N.new('ShaderNodeMath'); side.operation = 'GREATER_THAN'; side.inputs[1].default_value = 0.3
            L.new(dot.outputs['Value'], side.inputs[0])
            mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; L.new(fr.outputs[0], mm.inputs[0]); L.new(side.outputs[0], mm.inputs[1])
            ms = N.new('ShaderNodeMath'); ms.operation = 'MULTIPLY'; ms.inputs[1].default_value = 0.28; L.new(mm.outputs[0], ms.inputs[0])
            rm = N.new('ShaderNodeMix'); rm.data_type = 'RGBA'; rm.blend_type = 'SCREEN'; rm.location = (900, 0)
            L.new(ms.outputs[0], rm.inputs[0]); L.new(col, rm.inputs[6]); rm.inputs[7].default_value = hexc('#ffc79a')
            col = rm.outputs[2]
    em = N.new('ShaderNodeEmission'); em.location = (1100, 0); L.new(col, em.inputs[0])
    if alpha and tex is not None:
        a = t.outputs[1]
        if alpha == 'clip':
            g = N.new('ShaderNodeMath'); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = 0.5
            L.new(a, g.inputs[0]); a = g.outputs[0]
        tr = N.new('ShaderNodeBsdfTransparent'); ms = N.new('ShaderNodeMixShader'); ms.location = (1250, 0)
        L.new(a, ms.inputs[0]); L.new(tr.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2])
        L.new(ms.outputs[0], out.inputs[0])
    else:
        L.new(em.outputs[0], out.inputs[0])
    m.use_backface_culling = cull
    return m

def hull_mat(name, tex=None):
    m, nt = new_mat(name); N, L = nt.nodes, nt.links
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); em.inputs[0].default_value = LINE
    if tex is not None:
        t = N.new('ShaderNodeTexImage'); t.image = tex
        g = N.new('ShaderNodeMath'); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = 0.5; L.new(t.outputs[1], g.inputs[0])
        tr = N.new('ShaderNodeBsdfTransparent'); ms = N.new('ShaderNodeMixShader')
        L.new(g.outputs[0], ms.inputs[0]); L.new(tr.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2])
        L.new(ms.outputs[0], out.inputs[0])
    else:
        L.new(em.outputs[0], out.inputs[0])
    m.use_backface_culling = True
    return m

def invisible_mat():
    m, nt = new_mat('INVISIBLE'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(nt.nodes.new('ShaderNodeBsdfTransparent').outputs[0], out.inputs[0]); return m

def tex_of(m):
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.name.startswith('Mtoon1BaseColorTexture'): return n.image

def vrm_alpha(m):
    try:
        mt = m.vrm_addon_extension.mtoon1; return {'MASK': 'clip', 'BLEND': 'blend'}.get(mt.alpha_mode), mt.double_sided
    except Exception: return None, True

C = dict(hair=hexc('#2c2a36'), hair_sh=hexc('#1b1a23'), hair_hi=hexc('#5b5870'),
         hood=hexc('#4a4c57'), hood_sh=hexc('#30313c'), jean=hexc('#2c3346'), jean_sh=hexc('#1c2131'),
         red=hexc('#c4262e'), red_sh=hexc('#86161f'), hp=hexc('#18171c'), hp_sh=hexc('#0c0b0f'), hp_hi=hexc('#3c3a44'),
         string=hexc('#d2cdc4'), string_sh=hexc('#9c949a'), skin_sh=hexc('#e2b2ad'))
DARK_RAMP = [(0.0, hexc('#2a1c22')), (1.0, hexc('#5a4650'))]
IRIS_RAMP = [(0.0, hexc('#24130d')), (0.45, hexc('#5e321d')), (1.0, hexc('#c4874f'))]

def convert(obj):
    hulls = []
    for i, m in enumerate(obj.data.materials):
        if m is None: continue
        n = m.name; tex = tex_of(m); a, ds = vrm_alpha(m)
        if 'HAIR' in n:
            nm = toon_mat('Sam_Hair_' + str(i), C['hair'], C['hair_sh'], tex=tex, tex_mode='flat', alpha=a or 'clip',
                          highlight=C['hair_hi'])
            hulls.append(hull_mat('Line_Hair_' + str(i), tex))
        elif 'Tops' in n:
            nm = toon_mat('Sam_Hoodie_Body', C['hood'], C['hood_sh'], tex=tex, tex_mode='flat', alpha='clip')
            hulls.append(hull_mat('Line_Tops', tex))
        elif 'Bottoms' in n:
            nm = toon_mat('Sam_Jeans', C['jean'], C['jean_sh'], tex=tex, tex_mode='flat', alpha='clip')
            hulls.append(hull_mat('Line_Bottoms', tex))
        elif 'Shoes' in n:
            nm = toon_mat('Sam_Shoes', tex=tex, alpha='clip'); hulls.append(hull_mat('Line_Shoes', tex))
        elif 'SKIN' in n:
            nm = toon_mat('Sam_Skin_' + n.split('_')[3], tex=tex, shadow=C['skin_sh'], alpha=a)
            hulls.append(hull_mat('Line_Skin_' + str(i), tex if a else None))
        elif 'EyeIris' in n:
            nm = toon_mat('Sam_Iris', tex=tex, tex_mode='remap', ramp=IRIS_RAMP, lit_only=True, alpha=a); hulls.append(None)
        elif any(k in n for k in ('FaceBrow', 'FaceEyelash', 'FaceEyeline')):
            nm = toon_mat('Sam_' + n.split('_')[3], tex=tex, tex_mode='remap', ramp=DARK_RAMP, lit_only=True, alpha=a); hulls.append(None)
        else:  # eye white, highlight, mouth, extra
            nm = toon_mat('Sam_' + n.split('_')[3], tex=tex, lit_only=True, alpha=a); hulls.append(None)
        nm.use_backface_culling = not ds
        obj.data.materials[i] = nm
    return hulls

def add_outline(obj, hull_list, thick):
    """inverted-hull outline. hull_list aligned with material slots (None -> invisible hull)"""
    n = len(obj.data.materials); inv = None
    for h in hull_list:
        if h is None:
            inv = inv or bpy.data.materials.get('INVISIBLE') or invisible_mat(); h = inv
        obj.data.materials.append(h)
    md = obj.modifiers.new('Outline', 'SOLIDIFY')
    md.thickness = thick; md.offset = 1; md.use_flip_normals = True; md.use_rim = False
    md.material_offset = n; md.use_quality_normals = True
    return md

# patch: 'flat' tex mode means flat colour (texture only used for alpha)
_orig_toon = toon_mat
def toon_mat(name, color=None, shadow=None, tex=None, tex_mode='color', **kw):
    if tex_mode == 'flat':
        m = _orig_toon(name, color, shadow, tex=None, **{k: v for k, v in kw.items() if k != 'alpha'})
        if kw.get('alpha') and tex is not None:  # bolt texture alpha onto the flat material
            nt = m.node_tree; N, L = nt.nodes, nt.links
            out = [x for x in N if x.type == 'OUTPUT_MATERIAL'][0]; em = [x for x in N if x.type == 'EMISSION'][0]
            t = N.new('ShaderNodeTexImage'); t.image = tex
            g = N.new('ShaderNodeMath'); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = 0.5; L.new(t.outputs[1], g.inputs[0])
            tr = N.new('ShaderNodeBsdfTransparent'); ms = N.new('ShaderNodeMixShader')
            L.new(g.outputs[0], ms.inputs[0]); L.new(tr.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2])
            L.new(ms.outputs[0], out.inputs[0])
        return m
    return _orig_toon(name, color, shadow, tex=tex, tex_mode=tex_mode, **kw)

# face-skin outline lives on a duplicate holding only the skin faces
face_line = face.copy(); face_line.data = face.data.copy(); face_line.name = 'Face_Outline'; link(face_line)
skin_idx = [i for i, m in enumerate(face.data.materials) if 'Face_00_SKIN' in m.name][0]
delete_faces(face_line, lambda f: f.material_index != skin_idx)

hb_list = convert(body); add_outline(body, hb_list, 0.0016)
convert(face)
hh = convert(hair); add_outline(hair, hh, 0.0011)
face_line.data.materials.clear(); face_line.data.materials.append(hull_mat('Line_Face'))
for p_ in face_line.data.polygons: p_.material_index = 0
bm = bmesh.new(); bm.from_mesh(face_line.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(face_line.data); bm.free()
dmd = face_line.modifiers.new('OutlineShell', 'DISPLACE'); dmd.direction = 'NORMAL'; dmd.mid_level = 0; dmd.strength = -0.0012

hood_m = toon_mat('Sam_Hoodie', C['hood'], C['hood_sh'], cull=False)
string_m = toon_mat('Sam_Drawstring', C['string'], C['string_sh'])
red_m = toon_mat('Sam_Glasses_Red', C['red'], C['red_sh'], rim=False)
hp_m = toon_mat('Sam_Headphones', C['hp'], C['hp_sh'], highlight=None)
hp_pad = toon_mat('Sam_Headphone_Pad', hexc('#2a2830'), hexc('#141318'))
line_m = hull_mat('Line_Generic')

def outline_simple(obj, thick, mat):
    obj.data.materials.append(mat); obj.data.materials.append(line_m)
    md = obj.modifiers.new('Outline', 'SOLIDIFY'); md.thickness = thick; md.offset = 1
    md.use_flip_normals = True; md.use_rim = False; md.material_offset = 1; md.use_quality_normals = True

# lens material: barely visible
lens_m, nt = new_mat('Sam_Lens'); N, L = nt.nodes, nt.links
o_ = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); em.inputs[0].default_value = hexc('#fff6ec')
tr = N.new('ShaderNodeBsdfTransparent'); ms = N.new('ShaderNodeMixShader'); ms.inputs[0].default_value = 0.07
L.new(tr.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2]); L.new(ms.outputs[0], o_.inputs[0])
lens_m.surface_render_method = 'BLENDED'

tops_i = [i for i, m in enumerate(body.data.materials) if m.name == 'Sam_Hoodie_Body'][0]
neck0 = arm.data.bones['J_Bip_C_Neck'].head_local
gname = {g.index: g.name for g in body.vertex_groups}
bm = bmesh.new(); bm.from_mesh(body.data); dl0 = bm.verts.layers.deform.active
def up_arm(v): return sum(w for gi, w in v[dl0].items() if 'UpperArm' in gname[gi] or 'LowerArm' in gname[gi]) > 0.35
kill = [f for f in bm.faces if f.material_index == tops_i and (all(up_arm(v) for v in f.verts) or
        all(v.co.z > neck0.z - 0.018 and abs(v.co.x) < 0.08 for v in f.verts))]
print('removed tops faces', len(kill))
bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(body.data); bm.free()

# ---------------------------------------------------------------- hoodie: long sleeves (shell of the arm skin)
groups = {g.index: g.name for g in body.vertex_groups}
ARMG = ('UpperArm', 'LowerArm'); HANDG = ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little')
sleeve = body.copy(); sleeve.data = body.data.copy(); sleeve.name = 'Hoodie_Sleeves'; link(sleeve)
sleeve.modifiers.remove(sleeve.modifiers['Outline'])
skin_body = [i for i, m in enumerate(body.data.materials) if m.name.startswith('Sam_Skin')][0]
def armish(v):
    a = sum(g.weight for g in v.groups if any(k in groups[g.group] for k in ARMG))
    h = sum(g.weight for g in v.groups if any(k in groups[g.group] for k in HANDG))
    return a > 0.5 and h < 0.15
bm = bmesh.new(); bm.from_mesh(sleeve.data); dl = bm.verts.layers.deform.active
def armish_bm(v):
    a = sum(w for gi, w in v[dl].items() if any(k in groups[gi] for k in ARMG))
    h = sum(w for gi, w in v[dl].items() if any(k in groups[gi] for k in HANDG))
    return a > 0.5 and h < 0.05
keep = [f for f in bm.faces if f.material_index == skin_body and all(armish_bm(v) for v in f.verts)]
kill = [f for f in bm.faces if f not in set(keep)]
bmesh.ops.delete(bm, geom=kill, context='FACES')
bm.normal_update()
for v in bm.verts: v.co += v.normal * 0.011
for f in bm.faces: f.material_index = 0
bm.to_mesh(sleeve.data); bm.free()
sleeve.data.materials.clear(); sleeve.data.materials.append(hood_m); sleeve.data.materials.append(line_m)
md = sleeve.modifiers.new('Outline', 'SOLIDIFY'); md.thickness = 0.0016; md.offset = 1; md.use_flip_normals = True
md.use_rim = False; md.material_offset = 1
print('sleeve faces', len(sleeve.data.polygons))

# ---------------------------------------------------------------- hood (down, bunched behind the neck)
neck = arm.data.bones['J_Bip_C_Neck'].head_local
def curve_to_mesh(cobj, name):
    bpy.context.view_layer.update()
    ev = cobj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = bpy.data.meshes.new_from_object(ev); me.name = name
    o = link(bpy.data.objects.new(name, me)); o.matrix_world = cobj.matrix_world.copy()
    bpy.data.objects.remove(cobj); return o
# hood roll: a tapered tube around the neck base, thick at the back, thin at the front V
pts, rads = [], []
for k in range(-33, 34):
    phi = math.radians(k * 5)                      # 0 = back (+Y), +-165 = front
    w = ((1 + math.cos(phi)) / 2) ** 1.2
    z = neck.z - 0.066 + 0.034 * w
    d = Vector((math.sin(phi), math.cos(phi), 0))
    c = Vector((0, neck.y + 0.004, z))
    hit = cast_in(bb, c, d)
    rr = min((hit - c).length if hit else 0.07, 0.085)
    r = 0.009 + 0.026 * w
    pts.append(c + d * (rr + r * 0.75) + Vector((0, 0, r * 0.35))); rads.append(r)
cu = curve_obj('Hoodie_HoodRoll_c', pts, 0.01, kind='POLY', res=4)
for sp_p, r in zip(cu.data.splines[0].points, rads): sp_p.radius = r / 0.01
cu.data.resolution_u = 2
hood = curve_to_mesh(cu, 'Hoodie_HoodRoll')
for p_ in hood.data.polygons: p_.use_smooth = True
# hood body: a rounded teardrop sheet lying on the upper back (shrinkwrapped to the body)
bm = bmesh.new(); ring = []
for k in range(40):
    t = 2 * math.pi * k / 40
    x = 0.105 * math.sin(t) * (0.75 + 0.25 * math.cos(t)); zz = 0.075 * math.cos(t) - 0.03 * math.cos(t) ** 2
    ring.append(bm.verts.new((x, 0, zz)))
f = bm.faces.new(ring); bmesh.ops.triangulate(bm, faces=[f])
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
pouch = mesh_obj('Hoodie_HoodBack', bm); pouch.location = (0, neck.y + 0.12, neck.z - 0.10)
pouch.rotation_euler = (math.radians(-8), 0, 0)
sw = pouch.modifiers.new('Drape', 'SHRINKWRAP'); sw.target = body; sw.wrap_method = 'PROJECT'
sw.use_project_y = True; sw.use_negative_direction = True; sw.use_positive_direction = True; sw.offset = 0.011
so = pouch.modifiers.new('Thick', 'SOLIDIFY'); so.thickness = 0.012; so.offset = 1
pouch.data.materials.append(hood_m); pouch.data.materials.append(line_m)
ol = pouch.modifiers.new('Outline', 'SOLIDIFY'); ol.thickness = 0.0016; ol.offset = 1; ol.use_flip_normals = True
ol.use_rim = False; ol.material_offset = 1
outline_simple(hood, 0.0016, hood_m)
for o in (hood, pouch): parent_bone(o, 'J_Bip_C_UpperChest')

# drawstrings
for s in (1, -1):
    pts = []
    for z, dx in ((neck.z - 0.055, 0.026), (neck.z - 0.10, 0.030), (neck.z - 0.15, 0.033), (neck.z - 0.19, 0.035)):
        hit = cast_in(bb, (s * dx, -1, z), (0, 1, 0)); y = (hit.y if hit else -0.1) - 0.005
        pts.append(Vector((s * dx, y, z)))
    st = curve_obj('Hoodie_String_' + ('L' if s > 0 else 'R'), pts, 0.0022, kind='BEZIER')
    st.data.materials.append(string_m)
    bm = cyl_bm(0.0034, 0.013, 16); ag = mesh_obj('Hoodie_Aglet_' + ('L' if s > 0 else 'R'), bm)
    ag.location = pts[-1] + Vector((0, 0, -0.008)); outline_simple(ag, 0.0008, string_m)
    for o in (st, ag): parent_bone(o, 'J_Bip_C_UpperChest')

# ---------------------------------------------------------------- glasses
nose = cast_in(fb, (0, -1, ez - 0.012), (0, 1, 0)).y
fy = min(face_front - 0.013, nose - 0.005)
print('nose', nose, 'fy', fy)
LW, LH, CR = 0.044, 0.024, 0.006
def wrap_y(x): return fy + 1.1 * x * x
def rrect(cx, cz):
    pts = []
    corners = [(cx + LW/2 - CR, cz + LH/2 - CR, 0), (cx - LW/2 + CR, cz + LH/2 - CR, 90),
               (cx - LW/2 + CR, cz - LH/2 + CR, 180), (cx + LW/2 - CR, cz - LH/2 + CR, 270)]
    for (x0, z0, a0) in corners:
        for k in range(7):
            a = math.radians(a0 + 90 * k / 6); x = x0 + CR * math.cos(a); z = z0 + CR * math.sin(a)
            pts.append(Vector((x, wrap_y(x), z)))
    return pts
glasses = []
lens_cz = ez - 0.002
for s, e in ((1, eyeL), (-1, eyeR)):
    cx = e.x + s * 0.002
    fr = curve_obj('Glasses_Frame_' + ('L' if s > 0 else 'R'), rrect(cx, lens_cz), 0.0013, cyclic=True)
    fr.data.materials.append(red_m); glasses.append(fr)
    bm = bmesh.new(); vs = [bm.verts.new(p + Vector((0, 0.0005, 0))) for p in rrect(cx, lens_cz)]; bm.faces.new(vs)
    ln = mesh_obj('Glasses_Lens_' + ('L' if s > 0 else 'R'), bm); ln.data.materials.append(lens_m); glasses.append(ln)
    # temple arm: outer top corner back to above the ear
    x0 = cx + s * LW / 2; z0 = lens_cz + LH / 2 - 0.006
    side = cast_in(fb, (s * 0.4, fy + 0.025, z0), (-s, 0, 0)); sx = (side.x if side else s * 0.07) + s * 0.004
    side2 = cast_in(fb, (s * 0.4, head_c.y + 0.01, z0 - 0.006), (-s, 0, 0)); sx2 = (side2.x if side2 else s * 0.072) + s * 0.004
    tp = [Vector((x0, wrap_y(x0), z0)), Vector((sx, fy + 0.012, z0)), Vector((sx, fy + 0.03, z0)),
          Vector((sx2, head_c.y + 0.02, z0 - 0.006)), Vector((sx2 - s * 0.004, head_c.y + 0.035, z0 - 0.02))]
    te = curve_obj('Glasses_Temple_' + ('L' if s > 0 else 'R'), tp, 0.0011, kind='BEZIER'); te.data.materials.append(red_m)
    glasses.append(te)
ix = eyeL.x - LW / 2 + 0.002
br = curve_obj('Glasses_Bridge', [Vector((ix, wrap_y(ix), lens_cz + 0.006)), Vector((0, fy - 0.002, lens_cz + 0.009)),
                                   Vector((-ix, wrap_y(ix), lens_cz + 0.006))], 0.0012, kind='BEZIER')
br.data.materials.append(red_m); glasses.append(br)
for g in glasses: parent_bone(g, 'J_Bip_C_Head'); g.visible_shadow = False

# ---------------------------------------------------------------- headphones
cup_z = ez - 0.022; cup_y = head_c.y + 0.008
sideL = cast_in(hfb, (0.4, cup_y, cup_z), (-1, 0, 0)); sideR = cast_in(hfb, (-0.4, cup_y, cup_z), (1, 0, 0))
half = max(abs(sideL.x), abs(sideR.x)) + 0.004
CUP_R, CUP_D = 0.040, 0.026
hp_parts = []
for s in (1, -1):
    bm = cyl_bm(CUP_R, CUP_D); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
    cup = mesh_obj('Headphone_Cup_' + ('L' if s > 0 else 'R'), bm); cup.location = (s * (half + CUP_D / 2 + 0.006), cup_y, cup_z)
    outline_simple(cup, 0.0012, hp_m)
    bm = torus_bm(CUP_R - 0.009, 0.0085, 40, 12); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
    pad = mesh_obj('Headphone_Pad_' + ('L' if s > 0 else 'R'), bm); pad.location = (s * (half + 0.004), cup_y, cup_z)
    outline_simple(pad, 0.001, hp_pad)
    bm = cyl_bm(CUP_R * 0.62, 0.006); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
    cap = mesh_obj('Headphone_Cap_' + ('L' if s > 0 else 'R'), bm); cap.location = (s * (half + CUP_D + 0.007), cup_y, cup_z)
    outline_simple(cap, 0.0009, hp_pad)
    hp_parts += [cup, pad, cap]
# band: ellipse over the hair, fitted with ray casts
a = half + CUP_D / 2 + 0.006
need = []
for k in range(-14, 15):
    th = math.radians(k * 5)  # from vertical
    d = Vector((math.sin(th), 0, math.cos(th)))
    o = Vector((0, cup_y, cup_z)) + d * 0.6
    hit = cast_in(hfb, o, -d)
    need.append((th, (hit - Vector((0, cup_y, cup_z))).length + 0.010 if hit else 0))
rs = [r for _, r in need]
sm = [sorted(rs[max(0, i - 3):i + 4])[len(rs[max(0, i - 3):i + 4]) // 2] for i in range(len(rs))]  # median filter
sm = [sum(sm[max(0, i - 2):i + 3]) / len(sm[max(0, i - 2):i + 3]) for i in range(len(sm))]  # moving average
band_pts = [Vector((-a, 0, CUP_R - 0.006))]
for (th, _), r in zip(need, sm):
    if abs(th) <= math.radians(62): band_pts.append(Vector((math.sin(th) * r, 0, math.cos(th) * r)))
band_pts.append(Vector((a, 0, CUP_R - 0.006)))
b = max(p.z for p in band_pts)
band = curve_obj('Headphone_Band', band_pts, 0.0048, kind='BEZIER'); band.location = (0, cup_y, cup_z)
band.scale = (1, 2.0, 0.75 if False else 1)
band.data.materials.append(hp_m)
band_pad = curve_obj('Headphone_BandPad', [p * 0.965 for p in band_pts[3:-3]], 0.0042, kind='BEZIER'); band_pad.location = (0, cup_y, cup_z)
band_pad.scale = (1, 2.6, 1); band_pad.data.materials.append(hp_pad)
hp_parts += [band, band_pad]
print('headphone half', half, 'band a,b', a, b)
for p in hp_parts: parent_bone(p, 'J_Bip_C_Head')

# ---------------------------------------------------------------- pose
arm.data.pose_position = 'POSE'
for pb in arm.pose.bones: pb.matrix_basis = Matrix.Identity(4)
def upd(): bpy.context.view_layer.update()
def rot_world(name, axis, deg):
    upd(); pb = arm.pose.bones[name]; h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix
    upd()
def move_world(name, v):
    upd(); pb = arm.pose.bones[name]; pb.matrix = Matrix.Translation(Vector(v)) @ pb.matrix; upd()

def pose(look=True):
    for pb in arm.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    upd()
    move_world('J_Bip_L_Shoulder', (-0.008, 0, -0.002)); move_world('J_Bip_R_Shoulder', (0.008, 0, -0.002))
    rot_world('J_Bip_L_UpperArm', 'Y', 72); rot_world('J_Bip_R_UpperArm', 'Y', -72)
    rot_world('J_Bip_L_UpperArm', 'X', -4); rot_world('J_Bip_R_UpperArm', 'X', -4)
    rot_world('J_Bip_L_LowerArm', 'X', -8); rot_world('J_Bip_R_LowerArm', 'X', -8)
    for s in 'LR':  # lean arms
        pb = arm.pose.bones[f'J_Bip_{s}_UpperArm']; pb.scale = (0.88, 1, 0.88)
        pb = arm.pose.bones[f'J_Bip_{s}_Hand']; pb.scale = (1 / 0.88, 1, 1 / 0.88)
    upd()
    if look:
        rot_world('J_Bip_C_Neck', 'Z', -4); rot_world('J_Bip_C_Head', 'Z', -6)
        rot_world('J_Bip_C_Head', 'X', -5)
        for e in ('J_Adj_L_FaceEye', 'J_Adj_R_FaceEye'):
            rot_world(e, 'Z', -9); rot_world(e, 'X', -9)
pose(True)

# cable: from the left cup down into the hoodie front (built in posed space)
upd()
cupL = bpy.data.objects['Headphone_Cup_L'].matrix_world.translation
pin = bpy.data.objects['Hoodie_String_L'].matrix_world
chest = cast_in(bvh_of([body]), (0.05, -1, neck.z - 0.12), (0, 1, 0))
cable = curve_obj('Headphone_Cable', [cupL + Vector((0, -0.004, -CUP_R + 0.004)), cupL + Vector((-0.012, -0.03, -0.09)),
                                      Vector((0.07, chest.y - 0.015, neck.z - 0.07)), Vector((0.06, chest.y - 0.006, neck.z - 0.16)),
                                      Vector((0.055, chest.y + 0.004, neck.z - 0.24))], 0.0018, kind='BEZIER')
cable.data.materials.append(hp_m); cable.visible_shadow = False

# ---------------------------------------------------------------- lights, world, render
for o in [o for o in bpy.data.objects if o.type in ('LIGHT', 'CAMERA')]: bpy.data.objects.remove(o)
sun_d = bpy.data.lights.new('Sun_GoldenHour', 'SUN'); sun_d.energy = 3.0; sun_d.color = (1.0, 0.82, 0.62); sun_d.angle = math.radians(0.5); sun_d.use_shadow = False
sun = link(bpy.data.objects.new('Sun_GoldenHour', sun_d))
Ldir = Vector((-0.42, -0.84, 0.30)).normalized()  # light comes FROM screen-left/front, low
sun.rotation_euler = Ldir.to_track_quat('Z', 'Y').to_euler()
world = bpy.data.worlds.new('Sam_World'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1)
sc.render.engine = 'BLENDER_EEVEE'
sc.eevee.taa_render_samples = 48
sc.eevee.shadow_resolution_scale = 1.0
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
bpy.ops.wm.save_as_mainfile(filepath=ROOT + 'sam_toon.blend')
print('SAVED')
