"""Toon Sam (CC0 VRoid base + our hoodie/glasses/headphones) seated on the mamachari with IK.
exec() after toonlib_v4 + bike.py.  load_sam(B) -> rig;  seat_rider(rig, B, lean);  report(rig, B)"""
SAM_BLEND = next(p for p in (os.path.join(D, 'sam_toon.blend'), os.path.join(D, '..', '..', '..', 'assets', 'toon_sam', 'sam_toon.blend')) if os.path.exists(p))
HIPX = 0.03
PB = lambda rig, n: rig.pose.bones[n]


def load_sam(B):
    with bpy.data.libraries.load(SAM_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    rig = None
    for o in dst.objects:
        if o is None or o.type in ('LIGHT', 'CAMERA'): continue
        sc.collection.objects.link(o)
        if o.type == 'EMPTY': o.hide_render = True
        if o.type == 'ARMATURE': rig = o
    rig.parent = B['root']
    rig.rotation_mode = 'XYZ'; rig.rotation_euler = (0, 0, math.radians(90))          # model faces -Y; +90 turns it to face +X (its left = bike +Y)
    rig.data.pose_position = 'POSE'
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    return rig


def _empty_at(name, parent, loc):
    e = empty(name, parent, loc); return e


def _rot_arm(rig, name, axis, deg):
    """rotate a pose bone about an ARMATURE-space axis through its head (parents first)"""
    pb = PB(rig, name); bpy.context.view_layer.update()
    R = Matrix.Rotation(math.radians(deg), 4, Vector(axis))
    pb.matrix = Matrix.Translation(pb.head) @ R @ Matrix.Translation(-pb.head) @ pb.matrix
    bpy.context.view_layer.update()


def _curl_fingers(rig, side, amount=1.0):
    """curl each finger joint toward the palm: pick the local axis that moves the tip most toward armature -Z
    (T-pose palms face down), so it works whatever the VRoid bone roll is"""
    S = 'L' if side > 0 else 'R'
    for fn, ang in (('Index', 62), ('Middle', 66), ('Ring', 68), ('Little', 70)):
        for j, k in ((1, 1.0), (2, 1.0), (3, 0.8)):
            pb = PB(rig, 'J_Bip_%s_%s%d' % (S, fn, j)); best = None
            for ax in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
                q = Quaternion(ax, math.radians(30))
                pb.rotation_quaternion = q; bpy.context.view_layer.update()
                z = pb.tail.z
                if best is None or z < best[0]: best = (z, ax)
                pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_quaternion = Quaternion(best[1], math.radians(ang * k * amount))
    for j, ang in ((1, 20), (2, 25), (3, 25)):
        pb = PB(rig, 'J_Bip_%s_Thumb%d' % (S, j)); best = None
        for ax in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)):
            pb.rotation_quaternion = Quaternion(ax, math.radians(30)); bpy.context.view_layer.update()
            z = pb.tail.z
            if best is None or z < best[0]: best = (z, ax)
            pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_quaternion = Quaternion(best[1], math.radians(ang * amount))
    bpy.context.view_layer.update()


IKT = {}
WRIST_OUT = 0.062


def seat_rider(rig, B, lean=30, head_pitch=-6):
    IKT.clear(); bpy.context.view_layer.update()
    # 1) torso: lean forward from the hips, head looks down the road
    _rot_arm(rig, 'J_Bip_C_Spine', (1, 0, 0), lean * 0.55)
    _rot_arm(rig, 'J_Bip_C_Chest', (1, 0, 0), lean * 0.30)
    _rot_arm(rig, 'J_Bip_C_UpperChest', (1, 0, 0), lean * 0.15)
    _rot_arm(rig, 'J_Bip_C_Neck', (1, 0, 0), -lean * 0.45)
    _rot_arm(rig, 'J_Bip_C_Head', (1, 0, 0), -lean * 0.35 - head_pitch)
    # arms down from T-pose toward the bars first (helps the IK pick a natural solution)
    _rot_arm(rig, 'J_Bip_L_UpperArm', (0, 1, 0), 55); _rot_arm(rig, 'J_Bip_R_UpperArm', (0, 1, 0), -55)
    # 2) sit: pelvis centre 0.11 above the saddle top, a touch behind the saddle centre
    rig.location = (0, 0, 0); bpy.context.view_layer.update()
    hips_w = rig.matrix_world @ PB(rig, 'J_Bip_C_Hips').head
    want = B['root'].matrix_world @ (B['saddle'] + Vector((HIPX, 0, 0.035 + 0.105)))
    rig.location = B['root'].matrix_world.inverted().to_3x3() @ (want - hips_w)
    bpy.context.view_layer.update()
    # 3) IK: wrists to the grips (elbows out and slightly down), ankles over the pedals (knees forward + out)
    steer, crank = B['steer'], B['crank']
    for side, S, gi in ((1, 'L', 0), (-1, 'R', 1)):      # side = bike Y of that limb
        g = B['grips'][gi]
        # wrap grip: wrist just outboard of and above the rubber, hand pointing inward across it, palm down on it
        wt = _empty_at('ik_hand_' + S, steer, g - HT_B + Vector((-0.012, side * WRIST_OUT, 0.032)))
        pt = _empty_at('pole_elbow_' + S, B['root'], Vector((0.25, side * 0.75, 1.05)))
        c = PB(rig, 'J_Bip_%s_LowerArm' % S).constraints.new('IK')
        c.target = wt; c.pole_target = pt; c.chain_count = 2; c.pole_angle = math.radians(0)
        ht = _empty_at('aim_hand_' + S, steer, g - HT_B + Vector((0.035, -side * 0.10, -0.018)))
        hc = PB(rig, 'J_Bip_%s_Hand' % S).constraints.new('DAMPED_TRACK'); hc.target = ht; hc.track_axis = 'TRACK_Y'
        # roll: the palm (the hand axis nearest armature -Z in the T-pose) faces down onto the bar
        hb = rig.data.bones['J_Bip_%s_Hand' % S]; R0 = hb.matrix_local.to_3x3()
        best = max((('TRACK_X', R0.col[0]), ('TRACK_NEGATIVE_X', -R0.col[0]), ('TRACK_Z', R0.col[2]), ('TRACK_NEGATIVE_Z', -R0.col[2])),
                   key=lambda a: a[1].dot(Vector((0, 0, -1))))
        dn = _empty_at('palm_dn_' + S, steer, g - HT_B + Vector((0.0, side * 0.02, -0.25)))
        lc = PB(rig, 'J_Bip_%s_Hand' % S).constraints.new('LOCKED_TRACK'); lc.target = dn; lc.lock_axis = 'LOCK_Y'; lc.track_axis = best[0]
        IKT['hand_' + S] = wt
        p = B['pedals'][gi] - BB
        at = _empty_at('ik_ankle_' + S, crank, p + Vector((-0.045, side * 0.0, 0.085)))
        kp = _empty_at('pole_knee_' + S, B['root'], Vector((1.2, side * 0.32, 0.75)))
        c = PB(rig, 'J_Bip_%s_LowerLeg' % S).constraints.new('IK')
        c.target = at; c.pole_target = kp; c.chain_count = 2; c.pole_angle = math.radians(-112 if S == 'L' else -68)   # knees forward, a hand's width apart
        tt = _empty_at('aim_toe_' + S, crank, p + Vector((0.14, side * 0.0, 0.035)))
        fc = PB(rig, 'J_Bip_%s_Foot' % S).constraints.new('DAMPED_TRACK'); fc.target = tt; fc.track_axis = 'TRACK_Y'
        IKT['ankle_' + S] = at
        _curl_fingers(rig, 1 if S == 'L' else -1)
    bpy.context.view_layer.update()
    return dict(IKT)


def report(rig, B):
    bpy.context.view_layer.update()
    mw = rig.matrix_world
    for S in ('L', 'R'):
        w = mw @ PB(rig, 'J_Bip_%s_LowerArm' % S).tail; t = IKT['hand_' + S].matrix_world.translation
        a = mw @ PB(rig, 'J_Bip_%s_LowerLeg' % S).tail; u = IKT['ankle_' + S].matrix_world.translation
        el = mw @ PB(rig, 'J_Bip_%s_LowerArm' % S).head; kn = mw @ PB(rig, 'J_Bip_%s_LowerLeg' % S).head
        print('IK %s wrist err %.3f ankle err %.3f elbow %s knee %s' % (S, (w - t).length, (a - u).length,
              tuple(round(x, 2) for x in el), tuple(round(x, 2) for x in kn)))
    print('hips', tuple(round(x, 3) for x in (mw @ PB(rig, 'J_Bip_C_Hips').head)), 'head', tuple(round(x, 3) for x in (mw @ PB(rig, 'J_Bip_C_Head').head)))
