"""Shared toon setup + helpers extracted from the locked shot 01 v4 build (SHOT_RULES). exec() it after setting OUT/SCALE."""
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix, Euler, Quaternion
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = int(SCALE * 100)
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
try:
    sc.eevee.taa_render_samples = 16
except Exception:
    pass
W = bpy.data.worlds.new('w'); sc.world = W
W.use_nodes = True
bg = W.node_tree.nodes.get('Background')
bg.inputs[0].default_value = (0.32, 0.25, 0.42, 1); bg.inputs[1].default_value = 0.12

# ---------------- materials ----------------
SUNV = tuple(Vector((-0.62, 1.0, 0.24)).normalized())
def toon(name, shadow, lit, rim=None, tex=None, rimfacing=0.40):
    """2-tone cel ramp (+ optional 3rd bright rim tone). tex: callable(nt, ramp_in) -> socket overriding colours"""
    lin = lambda c: tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
    shadow, lit = lin(shadow), lin(lit); rim = lin(rim) if rim else None
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial')
    dif = N.new('ShaderNodeBsdfDiffuse')
    s2r = N.new('ShaderNodeShaderToRGB')
    bw = N.new('ShaderNodeRGBToBW')
    L.new(dif.outputs[0], s2r.inputs[0]); L.new(s2r.outputs[0], bw.inputs[0])
    half = N.new('ShaderNodeMath'); half.operation = 'MULTIPLY'; half.inputs[1].default_value = 0.5
    L.new(bw.outputs[0], half.inputs[0])
    ramp = N.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
    e = ramp.color_ramp.elements
    e[0].position = 0.0; e[0].color = (*shadow, 1)
    e[1].position = 0.035; e[1].color = (*lit, 1)
    if rim:
        x = e.new(0.075); x.color = (*rim, 1)
    L.new(half.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]
    if tex:
        col = tex(nt, ramp)
    if rim:
        # crisp warm rim on silhouette edges that face the low sun (classic backlit anime rim)
        geo = N.new('ShaderNodeNewGeometry')
        lw = N.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.5
        dt = N.new('ShaderNodeVectorMath'); dt.operation = 'DOT_PRODUCT'; dt.inputs[1].default_value = SUNV
        L.new(geo.outputs['Normal'], dt.inputs[0])
        g1 = N.new('ShaderNodeMath'); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = rimfacing
        L.new(lw.outputs['Facing'], g1.inputs[0])
        g2 = N.new('ShaderNodeMath'); g2.operation = 'GREATER_THAN'; g2.inputs[1].default_value = -0.15
        L.new(dt.outputs['Value'], g2.inputs[0])
        mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'
        L.new(g1.outputs[0], mm.inputs[0]); L.new(g2.outputs[0], mm.inputs[1])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        L.new(mm.outputs[0], mx.inputs[0]); L.new(col, mx.inputs[6]); mx.inputs[7].default_value = (*rim, 1)
        col = mx.outputs[2]
    em = N.new('ShaderNodeEmission'); L.new(col, em.inputs[0]); em.inputs[1].default_value = 1.0
    L.new(em.outputs[0], out.inputs[0])
    return m


def rusty(nt, ramp):
    """paint -> rust streaks: multiply the cel colour by a rust mask (streaks run along local Z = down the horn)"""
    N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (9, 9, 1.6)
    L.new(tc.outputs['Object'], mp.inputs[0])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 6
    L.new(mp.outputs[0], nz.inputs[0])
    st = N.new('ShaderNodeValToRGB'); st.color_ramp.interpolation = 'CONSTANT'
    st.color_ramp.elements[0].position = 0; st.color_ramp.elements[0].color = (1, 1, 1, 1)
    st.color_ramp.elements[1].position = 0.62; st.color_ramp.elements[1].color = (0.62, 0.36, 0.24, 1)
    q = st.color_ramp.elements.new(0.7); q.color = (0.45, 0.24, 0.17, 1)
    L.new(nz.outputs[0], st.inputs[0])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    L.new(ramp.outputs[0], mx.inputs[6]); L.new(st.outputs[0], mx.inputs[7])
    return mx.outputs[2]


def emis(name, c, s=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes
    for n in list(N): N.remove(n)
    o = N.new('ShaderNodeOutputMaterial'); e = N.new('ShaderNodeEmission')
    e.inputs[0].default_value = (*c, 1); e.inputs[1].default_value = s
    m.node_tree.links.new(e.outputs[0], o.inputs[0]); return m


INKC = (0.10, 0.06, 0.08)
ink = emis('ink', INKC)
ink.use_backface_culling = True
PAINT = toon('paint', (0.27, 0.25, 0.37), (0.62, 0.66, 0.60), (1.0, 0.80, 0.55), rusty)
INSIDE = toon('inside', (0.07, 0.06, 0.08), (0.20, 0.17, 0.18), (0.55, 0.40, 0.32))
CONC = toon('concrete', (0.27, 0.25, 0.33), (0.55, 0.52, 0.55), (1.0, 0.78, 0.55))
STEEL = toon('steel', (0.20, 0.19, 0.25), (0.42, 0.42, 0.47), (1.0, 0.82, 0.6))
CROW = toon('crow', (0.07, 0.07, 0.11), (0.20, 0.21, 0.32), (1.0, 0.66, 0.45))
CROWW = toon('croww', (0.07, 0.07, 0.11), (0.20, 0.21, 0.32))
BEAK = toon('beak', (0.03, 0.03, 0.04), (0.10, 0.10, 0.13), (0.9, 0.7, 0.5))
EYEW = emis('eyehi', (1, 0.95, 0.85), 1.0)
EYE = emis('eye', (0.02, 0.02, 0.03))
WIRE = emis('wire', (0.08, 0.05, 0.07))


def outline(ob, t=0.006):
    ob.data.materials.append(ink)
    sm = ob.modifiers.new('ol', 'SOLIDIFY'); sm.thickness = -t if False else t
    sm.offset = 1; sm.use_flip_normals = True; sm.material_offset = len(ob.data.materials) - 1
    sm.use_rim = False


def mesh_obj(name, bm, mat, parent=None, line=0.006):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    me.materials.append(mat)
    if line: outline(ob, line)
    if parent: ob.parent = parent
    return ob


def lathe(prof, seg=56, cap_back=True):
    """prof: [(y, r)] along +Y; returns bmesh"""
    bm = bmesh.new(); rings = []
    for y, r in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * i / seg), y, r * math.sin(2 * math.pi * i / seg))) for i in range(seg)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_back:
        bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def ellipsoid(sx, sy, sz, seg=24, ring=14):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    return bm


def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e)
    e.parent = parent; e.location = loc; e.empty_display_size = .02
    return e


