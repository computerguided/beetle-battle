"""Procedural poison-dart frog, rendered from above as animation frames.

    blender -b -P frog.py -- OUT_DIR [--preview] [--res N]

The frog is rebuilt from scratch for every pose: a lofted body, skin-modifier
limbs with toes, eyes.  Two colour morphs are rendered (a strawberry red and
an azure blue) plus one set of normal maps.
"""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector

FRAME_SIZE = 2.2          # world units covered by one frame
FRAME_CY = -0.42          # frame centre (the frog's body centre is at y = 0)

# ----------------------------------------------------------------------------
# poses (right-hand side; the left side is mirrored)
# ----------------------------------------------------------------------------
def P(**k):
    return k

FORE_SIT = P(S=(0.15, 0.15, 0.09), E=(0.285, 0.07, 0.11), W=(0.265, 0.27, 0.03), dir=-22)
HIND_SIT = P(H=(0.10, -0.36, 0.09), K=(0.315, -0.10, 0.12), A=(0.245, -0.44, 0.05), T=(0.375, -0.25, 0.025), dir=28)
BODY_SIT = P(sx=1.0, sy=1.0, sz=1.0, puff=0.0, dy=0.0)

POSES = {
    'sit':    P(body=BODY_SIT, fore=FORE_SIT, hind=HIND_SIT),
    'puff':   P(body=P(sx=1.0, sy=1.0, sz=1.04, puff=1.0, dy=0.0), fore=FORE_SIT, hind=HIND_SIT),
    'croak':  P(body=P(sx=1.0, sy=1.0, sz=1.07, puff=2.0, dy=0.0), fore=FORE_SIT, hind=HIND_SIT),
    'crouch': P(body=P(sx=1.05, sy=0.97, sz=0.86, puff=0.0, dy=-0.02),
                fore=P(S=(0.15, 0.15, 0.08), E=(0.30, 0.08, 0.10), W=(0.27, 0.25, 0.03), dir=-22),
                hind=P(H=(0.10, -0.36, 0.08), K=(0.325, -0.13, 0.11), A=(0.25, -0.45, 0.05), T=(0.385, -0.27, 0.025), dir=30)),
    'launch': P(body=P(sx=0.97, sy=1.04, sz=1.0, puff=0.0, dy=0.03),
                fore=P(S=(0.15, 0.15, 0.09), E=(0.29, 0.03, 0.10), W=(0.31, 0.15, 0.07), dir=0),
                hind=P(H=(0.10, -0.36, 0.09), K=(0.29, -0.40, 0.10), A=(0.20, -0.70, 0.06), T=(0.235, -0.93, 0.035), dir=172)),
    'fly':    P(body=P(sx=0.94, sy=1.07, sz=0.97, puff=0.0, dy=0.05),
                fore=P(S=(0.15, 0.15, 0.09), E=(0.255, -0.03, 0.08), W=(0.215, -0.22, 0.07), dir=172),
                hind=P(H=(0.10, -0.36, 0.09), K=(0.175, -0.67, 0.09), A=(0.135, -0.98, 0.08), T=(0.125, -1.21, 0.07), dir=180)),
    'glide':  P(body=P(sx=0.96, sy=1.05, sz=0.98, puff=0.0, dy=0.04),
                fore=P(S=(0.15, 0.15, 0.09), E=(0.29, 0.10, 0.09), W=(0.27, 0.30, 0.08), dir=-5),
                hind=P(H=(0.10, -0.36, 0.09), K=(0.225, -0.62, 0.09), A=(0.185, -0.93, 0.08), T=(0.20, -1.15, 0.07), dir=176)),
    'tuck':   P(body=P(sx=1.0, sy=1.0, sz=1.0, puff=0.0, dy=0.02),
                fore=P(S=(0.15, 0.15, 0.09), E=(0.275, 0.20, 0.10), W=(0.225, 0.42, 0.06), dir=-8),
                hind=P(H=(0.10, -0.36, 0.09), K=(0.33, -0.32, 0.11), A=(0.22, -0.62, 0.07), T=(0.33, -0.80, 0.05), dir=150)),
    'land':   P(body=P(sx=1.07, sy=0.95, sz=0.84, puff=0.0, dy=-0.02),
                fore=P(S=(0.15, 0.15, 0.08), E=(0.33, 0.13, 0.10), W=(0.325, 0.31, 0.03), dir=-5),
                hind=P(H=(0.10, -0.36, 0.08), K=(0.345, -0.13, 0.11), A=(0.27, -0.47, 0.05), T=(0.405, -0.28, 0.025), dir=34)),
}


def lerp_pose(a, b, t):
    out = {}
    for part in a:
        out[part] = {}
        for k, va in a[part].items():
            vb = b[part][k]
            out[part][k] = tuple(x + (y - x) * t for x, y in zip(va, vb)) if isinstance(va, tuple) else va + (vb - va) * t
    return out


def walk_pose(phase):
    """Diagonal walking gait.  Returns (right, left) limb dictionaries."""
    def fore(ph):
        s, c = math.sin(ph), math.cos(ph)
        f = dict(FORE_SIT)
        lift = max(0.0, c) * 0.035
        f['W'] = (FORE_SIT['W'][0] - 0.012 * s, FORE_SIT['W'][1] + 0.10 * s, FORE_SIT['W'][2] + lift)
        f['E'] = (FORE_SIT['E'][0] + 0.01 * s, FORE_SIT['E'][1] + 0.05 * s, FORE_SIT['E'][2] + lift * 0.5)
        f['dir'] = FORE_SIT['dir'] - 6 * s
        return f

    def hind(ph):
        s, c = math.sin(ph), math.cos(ph)
        h = dict(HIND_SIT)
        lift = max(0.0, c) * 0.03
        h['K'] = (HIND_SIT['K'][0] + 0.012 * s, HIND_SIT['K'][1] + 0.05 * s, HIND_SIT['K'][2])
        h['A'] = (HIND_SIT['A'][0] - 0.01 * s, HIND_SIT['A'][1] + 0.085 * s, HIND_SIT['A'][2] + lift * 0.4)
        h['T'] = (HIND_SIT['T'][0] + 0.005 * s, HIND_SIT['T'][1] + 0.11 * s, HIND_SIT['T'][2] + lift)
        h['dir'] = HIND_SIT['dir'] - 5 * s
        return h
    a = phase * 2 * math.pi
    right = P(fore=fore(a), hind=hind(a + math.pi))
    left = P(fore=fore(a + math.pi), hind=hind(a))
    return right, left


def frame_list():
    """(name, right pose, left pose) for every animation frame, in atlas order."""
    frames = []
    def sym(name, pose):
        frames.append((name, pose, pose))
    sym('sit', POSES['sit'])
    sym('puff', POSES['puff'])
    for k in range(6):
        r, l = walk_pose(k / 6.0)
        body = P(sx=1.0, sy=1.0, sz=1.0, puff=0.0, dy=0.0, sway=math.sin(k / 6.0 * 2 * math.pi))
        frames.append(('walk%d' % k, P(body=body, **r), P(body=body, **l)))
    for name in ('crouch', 'launch', 'fly', 'glide', 'tuck', 'land', 'croak'):
        sym(name, POSES[name])
    sym('swim', lerp_pose(POSES['fly'], POSES['glide'], 0.6))
    return frames


# ----------------------------------------------------------------------------
# geometry
# ----------------------------------------------------------------------------
def catmull(pts, t):
    """pts: list of (t, value) with increasing t; smooth interpolation."""
    n = len(pts)
    for i in range(n - 1):
        if t <= pts[i + 1][0]:
            break
    p0 = pts[max(i - 1, 0)][1]; p1 = pts[i][1]; p2 = pts[i + 1][1]; p3 = pts[min(i + 2, n - 1)][1]
    span = pts[i + 1][0] - pts[i][0]
    u = min(max((t - pts[i][0]) / span, 0.0), 1.0)
    # monotone-ish Catmull-Rom (tangents scaled for non-uniform knots)
    m1 = (p2 - p0) / max(pts[i + 1][0] - pts[max(i - 1, 0)][0], 1e-6) * span
    m2 = (p3 - p1) / max(pts[min(i + 2, n - 1)][0] - pts[i][0], 1e-6) * span
    u2, u3 = u * u, u * u * u
    return (2 * u3 - 3 * u2 + 1) * p1 + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * p2 + (u3 - u2) * m2


# half-width, top and bottom of the body along the spine (t=0 snout, t=1 vent)
WIDTH = [(0, 0.115), (0.08, 0.158), (0.18, 0.205), (0.26, 0.218), (0.34, 0.210), (0.45, 0.236),
         (0.57, 0.252), (0.70, 0.228), (0.82, 0.172), (0.92, 0.120), (1.0, 0.090)]
TOP = [(0, 0.125), (0.08, 0.150), (0.18, 0.190), (0.27, 0.212), (0.40, 0.228), (0.55, 0.238),
       (0.72, 0.208), (0.86, 0.160), (0.95, 0.125), (1.0, 0.11)]
BOT = [(0, 0.035), (0.10, 0.02), (0.25, 0.012), (0.6, 0.010), (0.9, 0.02), (1.0, 0.03)]


def cap(t, e0=0.10, e1=0.085):
    """Rounds both ends of the loft off into half-ellipsoids."""
    if t < e0:
        u = 1 - t / e0
    elif t > 1 - e1:
        u = 1 - (1 - t) / e1
    else:
        return 1.0
    return math.sqrt(max(1 - u * u, 0.0))


def build_body(body, mat):
    M, K = 44, 28
    sx, sy, sz, puff, dy = body['sx'], body['sy'], body['sz'], body['puff'], body['dy']
    sway = body.get('sway', 0.0)
    verts, faces = [], []
    ts = [0.5 - 0.5 * math.cos(math.pi * (i + 0.6) / (M + 0.2)) for i in range(M)]
    for t in ts:
        cp = cap(t)
        w = max(catmull(WIDTH, t) * cp, 0.004) * sx
        top0, bot0 = catmull(TOP, t) * sz, catmull(BOT, t)
        top = (top0 + bot0) / 2 + (top0 - bot0) / 2 * max(cp, 0.03)
        bot = (top0 + bot0) / 2 - (top0 - bot0) / 2 * max(cp, 0.03)
        # breathing / calling: flanks and throat swell
        bulge = math.exp(-((t - 0.52) / 0.2) ** 2) * 0.035 * puff + math.exp(-((t - 0.17) / 0.08) ** 2) * 0.03 * puff
        w += bulge
        y = (0.5 - t) * sy + dy
        xoff = 0.012 * sway * math.sin((t - 0.2) * math.pi * 1.4)
        zc, h = (top + bot) / 2, (top - bot) / 2
        for k in range(K):
            a = 2 * math.pi * k / K
            ca, sa = math.cos(a), math.sin(a)
            # slightly flattened back, fuller flanks
            x = w * math.copysign(abs(ca) ** 0.85, ca)
            z = zc + h * math.copysign(abs(sa) ** 0.9, sa)
            verts.append((x + xoff, y, z))
    for i in range(M - 1):
        for k in range(K):
            a, b = i * K + k, i * K + (k + 1) % K
            faces.append((a, b, b + K, a + K))
    tip0 = len(verts); verts.append((0, 0.5 * sy + dy + 0.004, (TOP[0][1] * sz + BOT[0][1]) / 2))
    tip1 = len(verts); verts.append((0, -0.5 * sy + dy - 0.004, (TOP[-1][1] * sz + BOT[-1][1]) / 2))
    for k in range(K):
        faces.append((tip0, (k + 1) % K, k))
        faces.append((tip1, (M - 1) * K + k, (M - 1) * K + (k + 1) % K))
    ob = mesh_object('body', verts, faces, material=mat)
    add_subsurf(ob, 1)
    return ob


def skin_limb(name, pts, radii, edges, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(pts, edges, [])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new('skin', 'SKIN')
    m.use_smooth_shade = True
    for i, sv in enumerate(me.skin_vertices[0].data):
        sv.radius = (radii[i], radii[i])
        sv.use_root = (i == 0)
    add_subsurf(ob, 2)
    me.materials.append(mat)
    return ob


def rot2(dx, dy, deg):
    a = math.radians(deg)
    return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)


def digits(base, direction, spec, side):
    """Finger/toe end points fanned around `direction` (deg from +Y, + = outward)."""
    out = []
    for ang, length in spec:
        a = math.radians(direction + ang)
        out.append((base[0] + math.sin(a) * length, base[1] + math.cos(a) * length, 0.012))
    return out


FINGERS = [(-52, 0.075), (-18, 0.10), (14, 0.11), (48, 0.085)]
TOES = [(-62, 0.085), (-34, 0.125), (-8, 0.165), (18, 0.20), (46, 0.15)]


def build_side(pose, sign, mats, objs):
    def mx(p):
        return (p[0] * sign, p[1], p[2])
    f, h = pose['fore'], pose['hind']
    # ---- fore leg ----
    S, E, W = f['S'], f['E'], f['W']
    tips = digits(W, f['dir'], FINGERS, sign)
    pts = [mx(S), mx(E), mx(W)] + [mx(t) for t in tips]
    radii = [0.058, 0.040, 0.030] + [0.0125] * len(tips)
    edges = [(0, 1), (1, 2)] + [(2, 3 + i) for i in range(len(tips))]
    objs.append(skin_limb('fore', pts, radii, edges, mats['limb']))
    for t in tips:
        objs.append(pad_tip(mx(t), 0.021, mats['limb']))
    # ---- hind leg ----
    H, K, A, T = h['H'], h['K'], h['A'], h['T']
    tips = digits(T, h['dir'], TOES, sign)
    pts = [mx(H), mx(K), mx(A), mx(T)] + [mx(t) for t in tips]
    radii = [0.088, 0.062, 0.040, 0.030] + [0.013] * len(tips)
    edges = [(0, 1), (1, 2), (2, 3)] + [(3, 4 + i) for i in range(len(tips))]
    objs.append(skin_limb('hind', pts, radii, edges, mats['limb']))
    for t in tips:
        objs.append(pad_tip(mx(t), 0.022, mats['limb']))


_sphere_cache = {}


def pad_tip(loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=r, location=loc)
    ob = bpy.context.active_object
    ob.scale = (1, 1, 0.6)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def build_eyes(body, mats, objs):
    sy, dy, sz = body['sy'], body['dy'], body['sz']
    for sign in (-1, 1):
        y = (0.5 - 0.235) * sy + dy
        # socket bulge in skin colour, then the glossy eye itself
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.078, location=(sign * 0.150, y, 0.135 * sz))
        s = bpy.context.active_object
        s.scale = (0.95, 1.15, 0.9)
        bpy.ops.object.shade_smooth(); s.data.materials.append(mats['body']); objs.append(s)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.060, location=(sign * 0.172, y + 0.004, 0.165 * sz))
        e = bpy.context.active_object
        e.scale = (0.9, 1.1, 0.9)
        bpy.ops.object.shade_smooth(); e.data.materials.append(mats['eye']); objs.append(e)
    # nostrils
    for sign in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.011, location=(sign * 0.048, (0.5 - 0.055) * sy + dy, 0.118 * sz))
        nb = bpy.context.active_object
        nb.data.materials.append(mats['eye']); objs.append(nb)


def build_frog(right, left, mats):
    objs = [build_body(right['body'], mats['body'])]
    build_eyes(right['body'], mats, objs)
    build_side(right, 1, mats, objs)
    build_side(left, -1, mats, objs)
    return objs


# ----------------------------------------------------------------------------
# materials
# ----------------------------------------------------------------------------
MORPHS = {
    'red':  dict(body=(0.74, 0.022, 0.008), body2=(0.95, 0.11, 0.012), limb=(0.36, 0.012, 0.012), spot=(0.02, 0.004, 0.008)),
    'blue': dict(body=(0.006, 0.105, 0.72), body2=(0.02, 0.27, 0.95), limb=(0.006, 0.03, 0.30), spot=(0.003, 0.005, 0.03)),
}


def skin_material(name, base, base2, spot, spot_scale, spot_size, limb=False):
    mat, nt, bsdf = principled(name)
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    # warped voronoi cells -> irregular dark blotches
    warp = N.new('ShaderNodeTexNoise'); warp.inputs['Scale'].default_value = 5.0
    mix = N.new('ShaderNodeMixRGB'); mix.blend_type = 'ADD'; mix.inputs['Fac'].default_value = 0.11
    L.new(tc.outputs['Object'], warp.inputs['Vector'])
    L.new(tc.outputs['Object'], mix.inputs['Color1']); L.new(warp.outputs['Color'], mix.inputs['Color2'])
    vor = N.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = spot_scale
    L.new(mix.outputs['Color'], vor.inputs['Vector'])
    # per-cell random size so some cells have no spot at all
    cellrnd = N.new('ShaderNodeSeparateColor'); L.new(vor.outputs['Color'], cellrnd.inputs[0])
    thr = N.new('ShaderNodeMath'); thr.operation = 'MULTIPLY'; thr.inputs[1].default_value = spot_size
    L.new(cellrnd.outputs[0], thr.inputs[0])
    lt = N.new('ShaderNodeMath'); lt.operation = 'SUBTRACT'
    L.new(thr.outputs[0], lt.inputs[0]); L.new(vor.outputs['Distance'], lt.inputs[1])
    ramp = N.new('ShaderNodeMapRange'); ramp.inputs['From Min'].default_value = 0.0; ramp.inputs['From Max'].default_value = 0.03
    L.new(lt.outputs[0], ramp.inputs['Value'])
    # two-tone base: brighter along the back, deeper on the flanks
    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sep.inputs[0])
    up = N.new('ShaderNodeMapRange'); up.inputs['From Min'].default_value = 0.2; up.inputs['From Max'].default_value = 1.0
    L.new(sep.outputs['Z'], up.inputs['Value'])
    tone = N.new('ShaderNodeMixRGB'); tone.inputs['Color1'].default_value = (*base, 1); tone.inputs['Color2'].default_value = (*base2, 1)
    fine = N.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = 26.0; fine.inputs['Detail'].default_value = 3.0
    L.new(tc.outputs['Object'], fine.inputs['Vector'])
    fmul = N.new('ShaderNodeMath'); fmul.operation = 'MULTIPLY'
    L.new(up.outputs[0], fmul.inputs[0]); L.new(fine.outputs['Fac'], fmul.inputs[1])
    L.new(fmul.outputs[0], tone.inputs['Fac'])
    col = N.new('ShaderNodeMixRGB'); col.inputs['Color2'].default_value = (*spot, 1)
    L.new(tone.outputs[0], col.inputs['Color1']); L.new(ramp.outputs[0], col.inputs['Fac'])
    L.new(col.outputs[0], bsdf.inputs['Base Color'])
    set_input(bsdf, 'Roughness', 0.42)
    set_input(bsdf, ['Subsurface Weight', 'Subsurface'], 0.12)
    set_input(bsdf, 'Subsurface Radius', (0.06, 0.03, 0.02))
    set_input(bsdf, ['Subsurface Scale'], 1.0)
    set_input(bsdf, ['Specular IOR Level', 'Specular'], 0.25)
    # fine granular skin
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.12; bump.inputs['Distance'].default_value = 0.01
    L.new(fine.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs[0], bsdf.inputs['Normal'])
    return mat


def make_materials(morph):
    c = MORPHS[morph]
    eye, nt, bsdf = principled('eye')
    set_input(bsdf, 'Base Color', (0.004, 0.004, 0.005, 1)); set_input(bsdf, 'Roughness', 0.08)
    return {
        'body': skin_material('body_' + morph, c['body'], c['body2'], c['spot'], 8.5, 0.52),
        'limb': skin_material('limb_' + morph, c['limb'], c['limb'], c['spot'], 15.0, 0.38, limb=True),
        'eye': eye,
    }


# ----------------------------------------------------------------------------
def main():
    args = script_args()
    out = args[0]
    preview = '--preview' in args
    res = int(args[args.index('--res') + 1]) if '--res' in args else 384
    os.makedirs(out, exist_ok=True)
    reset_scene(samples=96 if not preview else 48, res=res)
    set_camera(FRAME_SIZE, 0.0, FRAME_CY)
    frames = frame_list()
    if preview:
        names = args[args.index('--preview') + 1].split(',') if len(args) > args.index('--preview') + 1 and not args[args.index('--preview') + 1].startswith('--') else ['sit', 'fly']
        frames = [f for f in frames if f[0] in names]
    mats = {m: make_materials(m) for m in MORPHS}
    for idx, (name, right, left) in enumerate(frames):
        for morph in MORPHS:
            clear_objects()
            build_frog(right, left, mats[morph])
            render_pair(os.path.join(out, 'frog_%s_%s' % (morph, name)), normal=(morph == 'red'))
    with open(os.path.join(out, 'frog_frames.txt'), 'w') as fh:
        fh.write('\n'.join(f[0] for f in frame_list()))


main()
