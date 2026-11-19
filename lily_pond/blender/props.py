"""Procedural pond props, rendered from above: lily pads, water-lily flowers,
bank rocks, a koi, a dragonfly and a tileable patch of grass.

    blender -b -P props.py -- OUT_DIR [what ...]     (what: pads flowers rocks grass koi dragonfly)
"""
import bpy, bmesh, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, noise


# ----------------------------------------------------------------------------
# lily pads
# ----------------------------------------------------------------------------
def pad_material(seed, hue):
    mat, nt, bsdf = principled('pad%d' % seed)
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    # polar coordinates around the stem
    ang = N.new('ShaderNodeMath'); ang.operation = 'ARCTAN2'
    L.new(sep.outputs['Y'], ang.inputs[0]); L.new(sep.outputs['X'], ang.inputs[1])
    rad = N.new('ShaderNodeVectorMath'); rad.operation = 'LENGTH'; L.new(tc.outputs['Object'], rad.inputs[0])
    # main veins: thin radial spokes that fade towards the rim
    nveins = 15 + seed % 4
    spoke = N.new('ShaderNodeMath'); spoke.operation = 'MULTIPLY'; spoke.inputs[1].default_value = nveins / 2.0
    L.new(ang.outputs[0], spoke.inputs[0])
    wob = N.new('ShaderNodeTexNoise'); wob.inputs['Scale'].default_value = 2.2
    L.new(tc.outputs['Object'], wob.inputs['Vector'])
    wadd = N.new('ShaderNodeMath'); wadd.operation = 'MULTIPLY_ADD'; wadd.inputs[1].default_value = 1.3
    L.new(wob.outputs['Fac'], wadd.inputs[0]); L.new(spoke.outputs[0], wadd.inputs[2])
    sn = N.new('ShaderNodeMath'); sn.operation = 'SINE'; L.new(wadd.outputs[0], sn.inputs[0])
    ab = N.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; L.new(sn.outputs[0], ab.inputs[0])
    vein = N.new('ShaderNodeMapRange'); vein.inputs['From Min'].default_value = 0.0; vein.inputs['From Max'].default_value = 0.16
    vein.inputs['To Min'].default_value = 1.0; vein.inputs['To Max'].default_value = 0.0
    L.new(ab.outputs[0], vein.inputs['Value'])
    fade = N.new('ShaderNodeMapRange'); fade.inputs['From Min'].default_value = 0.05; fade.inputs['From Max'].default_value = 0.95
    fade.inputs['To Min'].default_value = 1.0; fade.inputs['To Max'].default_value = 0.25
    L.new(rad.outputs['Value'], fade.inputs['Value'])
    vmul = N.new('ShaderNodeMath'); vmul.operation = 'MULTIPLY'
    L.new(vein.outputs[0], vmul.inputs[0]); L.new(fade.outputs[0], vmul.inputs[1])
    # fine net of secondary veins
    cells = N.new('ShaderNodeTexVoronoi'); cells.feature = 'DISTANCE_TO_EDGE'; cells.inputs['Scale'].default_value = 17.0
    L.new(tc.outputs['Object'], cells.inputs['Vector'])
    net = N.new('ShaderNodeMapRange'); net.inputs['From Min'].default_value = 0.0; net.inputs['From Max'].default_value = 0.07
    net.inputs['To Min'].default_value = 0.35; net.inputs['To Max'].default_value = 0.0
    L.new(cells.outputs['Distance'], net.inputs['Value'])
    allv = N.new('ShaderNodeMath'); allv.operation = 'MAXIMUM'
    L.new(vmul.outputs[0], allv.inputs[0]); L.new(net.outputs[0], allv.inputs[1])
    # colour: mottled greens, yellower veins, older (browner) towards the rim
    big = N.new('ShaderNodeTexNoise'); big.inputs['Scale'].default_value = 2.5; big.inputs['Detail'].default_value = 5.0
    L.new(tc.outputs['Object'], big.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB'); L.new(big.outputs['Fac'], ramp.inputs['Fac'])
    g = hue
    ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[0].color = (0.035 * g[0], 0.19 * g[1], 0.022 * g[2], 1)
    ramp.color_ramp.elements[1].position = 0.72; ramp.color_ramp.elements[1].color = (0.11 * g[0], 0.36 * g[1], 0.035 * g[2], 1)
    rim = N.new('ShaderNodeMapRange'); rim.inputs['From Min'].default_value = 0.86; rim.inputs['From Max'].default_value = 1.02
    L.new(rad.outputs['Value'], rim.inputs['Value'])
    rimn = N.new('ShaderNodeTexNoise'); rimn.inputs['Scale'].default_value = 7.0
    L.new(tc.outputs['Object'], rimn.inputs['Vector'])
    rimm = N.new('ShaderNodeMath'); rimm.operation = 'MULTIPLY'
    L.new(rim.outputs[0], rimm.inputs[0]); L.new(rimn.outputs['Fac'], rimm.inputs[1])
    aged = N.new('ShaderNodeMixRGB'); aged.inputs['Color2'].default_value = (0.30, 0.20, 0.035, 1)
    L.new(ramp.outputs['Color'], aged.inputs['Color1']); L.new(rimm.outputs[0], aged.inputs['Fac'])
    veincol = N.new('ShaderNodeMixRGB'); veincol.inputs['Color2'].default_value = (0.30 * g[0], 0.50 * g[1], 0.08, 1)
    vfac = N.new('ShaderNodeMath'); vfac.operation = 'MULTIPLY'; vfac.inputs[1].default_value = 0.62
    L.new(allv.outputs[0], vfac.inputs[0])
    L.new(aged.outputs[0], veincol.inputs['Color1']); L.new(vfac.outputs[0], veincol.inputs['Fac'])
    L.new(veincol.outputs[0], bsdf.inputs['Base Color'])
    set_input(bsdf, 'Roughness', 0.38)
    set_input(bsdf, ['Specular IOR Level', 'Specular'], 0.3)
    set_input(bsdf, ['Subsurface Weight', 'Subsurface'], 0.05)
    # veins are slightly sunken
    bump = N.new('ShaderNodeBump'); bump.invert = True; bump.inputs['Strength'].default_value = 0.5; bump.inputs['Distance'].default_value = 0.02
    L.new(allv.outputs[0], bump.inputs['Height']); L.new(bump.outputs[0], bsdf.inputs['Normal'])
    return mat


def pad_height(x, y, seed):
    """Gentle undulation of the leaf, raised rim, sunken veins."""
    r = math.hypot(x, y)
    a = math.atan2(y, x)
    nveins = 15 + seed % 4
    z = 0.012 * math.sin(a * 3 + seed) * r + 0.014 * math.sin(a * 5 + seed * 2.3) * r * r
    z += 0.030 * max(0.0, r - 0.72) ** 1.3 * 6          # slightly cupped rim
    z += 0.006 * noise.noise(Vector((x * 4 + seed, y * 4, seed)))
    z -= 0.010 * (1 - min(1.0, abs(math.sin(a * nveins / 2.0)) / 0.25)) * (1 - r) # vein grooves
    z += 0.02 * (1 - r)                                  # the middle sits on the stem
    return z


def build_pad(seed, hue):
    rnd = random.Random(seed)
    RINGS, SEGS = 48, 220
    notch_dir = 0.0
    notch_half = math.radians(rnd.uniform(2.5, 6.5))        # the characteristic slit
    notch_depth = rnd.uniform(0.86, 0.97)
    lobes = [(k, rnd.uniform(0.0, 0.02 / k), rnd.uniform(0, 6.28)) for k in range(2, 7)]
    verts, faces = [(0, 0, pad_height(0, 0, seed))], []
    for i in range(1, RINGS + 1):
        rr = (i / RINGS) ** 0.9
        for k in range(SEGS):
            a = -math.pi + 2 * math.pi * (k + 0.5) / SEGS
            edge = 1.0 + sum(amp * math.sin(kk * a + ph) for kk, amp, ph in lobes)
            edge += 0.006 * math.sin(a * 23 + seed) + 0.004 * math.sin(a * 41 + seed * 3)
            # cut the slit: pull the rim towards the centre near the notch direction
            d = abs((a - notch_dir + math.pi) % (2 * math.pi) - math.pi)
            if d < notch_half * 3:
                t = max(0.0, 1 - d / (notch_half * 3))
                edge *= 1 - notch_depth * t ** 1.6 * (0.15 + 0.85 * rr)
                # squeeze the angle away from the slit so its edges are crisp
            r = rr * edge
            x, y = r * math.cos(a), r * math.sin(a)
            verts.append((x, y, pad_height(x, y, seed)))
    for k in range(SEGS):
        faces.append((0, 1 + k, 1 + (k + 1) % SEGS))
    for i in range(RINGS - 1):
        for k in range(SEGS):
            a = 1 + i * SEGS + k; b = 1 + i * SEGS + (k + 1) % SEGS
            faces.append((a, a + SEGS, b + SEGS, b))
    ob = mesh_object('pad', verts, faces, material=pad_material(seed, hue))
    sol = ob.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.022; sol.offset = -1
    return ob


def add_droplets(seed, count):
    rnd = random.Random(seed * 7 + 1)
    mat, nt, bsdf = principled('drop')
    set_input(bsdf, 'Base Color', (0.9, 1.0, 0.95, 1)); set_input(bsdf, 'Roughness', 0.02)
    set_input(bsdf, ['Transmission Weight', 'Transmission'], 1.0); set_input(bsdf, 'IOR', 1.33)
    for _ in range(count):
        a, r = rnd.uniform(0.6, 5.7), rnd.uniform(0.15, 0.8)
        x, y = r * math.cos(a), r * math.sin(a)
        s = rnd.uniform(0.012, 0.035)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=s, location=(x, y, pad_height(x, y, seed) + s * 0.35))
        d = bpy.context.active_object
        d.scale = (1, rnd.uniform(0.8, 1.2), 0.55)
        bpy.ops.object.shade_smooth()
        d.data.materials.append(mat)


def render_pads(out):
    hues = [(1.0, 1.0, 1.0), (0.8, 1.06, 1.3), (1.25, 1.0, 0.8), (0.9, 0.92, 1.0), (1.1, 1.08, 1.0), (0.7, 0.98, 1.5)]
    set_camera(2.2)
    for i, hue in enumerate(hues):
        clear_objects()
        build_pad(11 + i * 5, hue)
        render_pair(os.path.join(out, 'pad_%d' % i), normal=False)
        # dew drops only exist in the normal map: in the game they catch the sun
        add_droplets(i, [7, 3, 12, 5, 2, 8][i])
        render_normal_only(os.path.join(out, 'pad_%d' % i))


# ----------------------------------------------------------------------------
# water-lily flowers
# ----------------------------------------------------------------------------
def petal(length, width, cup, tip_lift, mat, name='petal'):
    """A spoon-shaped petal lying along +X from the origin."""
    NU, NV = 14, 9
    verts, faces = [], []
    for i in range(NU + 1):
        u = i / NU
        w = width * math.sin(math.pi * u ** 0.75) ** 0.8 * (1 - 0.25 * u)
        for j in range(NV):
            v = j / (NV - 1) * 2 - 1
            x = u * length
            y = v * w
            z = cup * (v * v) * w * 2.2 + tip_lift * u * u * length
            verts.append((x, y, z))
    for i in range(NU):
        for j in range(NV - 1):
            a = i * NV + j
            faces.append((a, a + NV, a + NV + 1, a + 1))
    ob = mesh_object(name, verts, faces, material=mat)
    add_subsurf(ob, 1)
    return ob


def petal_material(name, inner, outer):
    mat, nt, bsdf = principled(name)
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.42
    L.new(sep.outputs['X'], mr.inputs['Value'])
    mix = N.new('ShaderNodeMixRGB'); mix.inputs['Color1'].default_value = (*inner, 1); mix.inputs['Color2'].default_value = (*outer, 1)
    L.new(mr.outputs[0], mix.inputs['Fac'])
    # faint lengthwise streaks
    wave = N.new('ShaderNodeTexWave'); wave.inputs['Scale'].default_value = 26.0; wave.bands_direction = 'Y'
    L.new(tc.outputs['Object'], wave.inputs['Vector'])
    st = N.new('ShaderNodeMixRGB'); st.blend_type = 'MULTIPLY'; st.inputs['Fac'].default_value = 0.025
    L.new(mix.outputs[0], st.inputs['Color1']); L.new(wave.outputs['Color'], st.inputs['Color2'])
    L.new(st.outputs[0], bsdf.inputs['Base Color'])
    set_input(bsdf, 'Roughness', 0.5)
    set_input(bsdf, ['Subsurface Weight', 'Subsurface'], 0.35)
    set_input(bsdf, 'Subsurface Radius', (0.1, 0.06, 0.06))
    # petals glow a little: they are thin and the sun shines through them
    L.new(st.outputs[0], bsdf.inputs['Emission Color'] if 'Emission Color' in bsdf.inputs else bsdf.inputs['Emission'])
    set_input(bsdf, 'Emission Strength', 0.07)
    return mat


def build_flower(seed, inner, outer, opened=1.0):
    rnd = random.Random(seed)
    mat = petal_material('petal%d' % seed, inner, outer)
    # rings of petals, outer ones flat and long, inner ones short and upright
    rings = [(9, 0.50, 0.185, 0.10, 0.02), (9, 0.44, 0.175, 0.35, 0.05), (8, 0.36, 0.155, 0.75, 0.09),
             (7, 0.27, 0.125, 1.25, 0.13), (6, 0.19, 0.10, 1.9, 0.16)]
    for ri, (count, length, width, lift, z0) in enumerate(rings):
        off = rnd.uniform(0, 6.28)
        for k in range(count):
            p = petal(length * rnd.uniform(0.92, 1.06) * opened, width * rnd.uniform(0.9, 1.1), 0.9, lift * rnd.uniform(0.85, 1.15), mat)
            p.rotation_euler = (rnd.uniform(-0.12, 0.12), 0, off + 2 * math.pi * k / count + rnd.uniform(-0.08, 0.08))
            p.location = (0, 0, z0)
    # golden stamens
    smat, nt, bsdf = principled('stamen')
    set_input(bsdf, 'Base Color', (1.0, 0.62, 0.03, 1)); set_input(bsdf, 'Roughness', 0.5)
    set_input(bsdf, ['Subsurface Weight', 'Subsurface'], 0.2)
    for k in range(46):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.0, 0.085) ** 0.8
        lean = r * 4.5
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.008, depth=0.12, location=(r * math.cos(a) * 1.3, r * math.sin(a) * 1.3, 0.22))
        s = bpy.context.active_object
        s.rotation_euler = (0, lean, a)
        s.data.materials.append(smat)


def render_flowers(out):
    set_camera(1.2)
    kinds = [((1.0, 0.86, 0.45), (1.0, 0.985, 0.97)),        # white, yellow heart
             ((1.0, 0.72, 0.60), (0.98, 0.42, 0.62)),        # pink
             ((1.0, 0.92, 0.75), (1.0, 0.78, 0.86))]         # blush
    for i, (inner, outer) in enumerate(kinds):
        clear_objects()
        build_flower(40 + i, inner, outer)
        render_pair(os.path.join(out, 'flower_%d' % i), samples=128)


# ----------------------------------------------------------------------------
# rocks for the bank
# ----------------------------------------------------------------------------
def rock_material(seed):
    mat, nt, bsdf = principled('rock%d' % seed)
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    n1 = N.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 3.0; n1.inputs['Detail'].default_value = 8.0; n1.inputs['Roughness'].default_value = 0.65
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB'); L.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    rnd = random.Random(seed)
    warm = rnd.uniform(-0.03, 0.05)
    dark = rnd.uniform(0.55, 1.0)
    ramp.color_ramp.elements[0].position = 0.34; ramp.color_ramp.elements[0].color = ((0.07 + warm) * dark, (0.068 + warm * 0.6) * dark, 0.066 * dark, 1)
    ramp.color_ramp.elements[1].position = 0.66; ramp.color_ramp.elements[1].color = ((0.50 + warm) * dark, (0.48 + warm * 0.6) * dark, 0.45 * dark, 1)
    # speckles
    sp = N.new('ShaderNodeTexNoise'); sp.inputs['Scale'].default_value = 60.0
    L.new(tc.outputs['Object'], sp.inputs['Vector'])
    spm = N.new('ShaderNodeMixRGB'); spm.blend_type = 'MULTIPLY'; spm.inputs['Fac'].default_value = 0.5
    L.new(ramp.outputs['Color'], spm.inputs['Color1']); L.new(sp.outputs['Color'], spm.inputs['Color2'])
    # moss where the surface faces up and the noise says so
    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sep.inputs[0])
    mn = N.new('ShaderNodeTexNoise'); mn.inputs['Scale'].default_value = 2.2; mn.inputs['Detail'].default_value = 6.0
    L.new(tc.outputs['Object'], mn.inputs['Vector'])
    mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'
    L.new(sep.outputs['Z'], mm.inputs[0]); L.new(mn.outputs['Fac'], mm.inputs[1])
    amount = rnd.uniform(0.44, 0.66)
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = amount; mr.inputs['From Max'].default_value = amount + 0.08
    L.new(mm.outputs[0], mr.inputs['Value'])
    mossn = N.new('ShaderNodeTexNoise'); mossn.inputs['Scale'].default_value = 40.0
    L.new(tc.outputs['Object'], mossn.inputs['Vector'])
    mossc = N.new('ShaderNodeValToRGB'); L.new(mossn.outputs['Fac'], mossc.inputs['Fac'])
    mossc.color_ramp.elements[0].color = (0.02, 0.06, 0.01, 1); mossc.color_ramp.elements[1].color = (0.09, 0.17, 0.025, 1)
    col = N.new('ShaderNodeMixRGB')
    L.new(spm.outputs[0], col.inputs['Color1']); L.new(mossc.outputs['Color'], col.inputs['Color2']); L.new(mr.outputs[0], col.inputs['Fac'])
    L.new(col.outputs[0], bsdf.inputs['Base Color'])
    set_input(bsdf, 'Roughness', 0.75)
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.4; bump.inputs['Distance'].default_value = 0.03
    L.new(sp.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs[0], bsdf.inputs['Normal'])
    return mat


def build_rock(seed):
    rnd = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0)
    ob = bpy.context.active_object
    sx, sy = rnd.uniform(0.62, 0.9), rnd.uniform(0.45, 0.8)
    off = Vector((rnd.uniform(0, 100), rnd.uniform(0, 100), rnd.uniform(0, 100)))
    for v in ob.data.vertices:
        p = v.co.copy()
        # chunky low-frequency shape, facets from cell noise, then fine grit
        d = 0.34 * noise.noise(p * 0.9 + off) + 0.15 * noise.noise(p * 2.3 + off * 2)
        cell = noise.voronoi(p * 1.5 + off, distance_metric='DISTANCE')[0][0]
        d += 0.30 * (cell - 0.45) + 0.03 * noise.noise(p * 9 + off)
        p = p * (1 + d)
        v.co = (p.x * sx, p.y * sy, max(p.z, -0.2) * 0.5)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(rock_material(seed))
    return ob


def render_rocks(out):
    set_camera(2.3)
    for i in range(8):
        clear_objects()
        build_rock(100 + i * 3)
        render_pair(os.path.join(out, 'rock_%d' % i))


# ----------------------------------------------------------------------------
# tileable grass
# ----------------------------------------------------------------------------
def render_grass(out, res=1024):
    """A dense lawn seen from above.  The blades are instanced on a square that
    is repeated around the camera, so the picture tiles seamlessly."""
    sc = bpy.context.scene
    clear_objects()
    T = 4.0                                              # tile size in world units
    rnd = random.Random(5)
    gmat, nt, bsdf = principled('grass')
    N, L = nt.nodes, nt.links
    info = N.new('ShaderNodeObjectInfo')
    ramp = N.new('ShaderNodeValToRGB'); L.new(info.outputs['Random'], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].color = (0.035, 0.13, 0.012, 1); ramp.color_ramp.elements[1].color = (0.20, 0.36, 0.04, 1)
    e = ramp.color_ramp.elements.new(0.5); e.color = (0.08, 0.24, 0.022, 1)
    L.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    set_input(bsdf, 'Roughness', 0.55)
    set_input(bsdf, ['Subsurface Weight', 'Subsurface'], 0.2)
    # soil underneath
    smat, snt, sb = principled('soil')
    set_input(sb, 'Base Color', (0.05, 0.10, 0.02, 1)); set_input(sb, 'Roughness', 0.9)
    bpy.ops.mesh.primitive_plane_add(size=T * 3, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(smat)
    # one mesh with all blades of a tile, then 3x3 copies for wrap-around
    verts, faces = [], []
    for _ in range(7500):
        x, y = rnd.uniform(-T / 2, T / 2), rnd.uniform(-T / 2, T / 2)
        clump = 0.5 + 0.5 * noise.noise(Vector((x * 1.57, y * 1.57, 0)))   # 1.57 ~ 2*pi/T: tiles
        h = rnd.uniform(0.25, 0.6) * (0.6 + clump)
        a = rnd.uniform(0, 6.28)
        lean = rnd.uniform(0.15, 0.55) * h
        w = rnd.uniform(0.018, 0.034)
        dx, dy = math.cos(a), math.sin(a)
        px_, py_ = -dy * w, dx * w
        base = len(verts)
        SEG = 4
        for s in range(SEG + 1):
            t = s / SEG
            cx, cy, cz = x + dx * lean * t * t, y + dy * lean * t * t, h * t * (1 - 0.25 * t)
            ww = (1 - t) ** 0.7
            verts.append((cx - px_ * ww, cy - py_ * ww, cz))
            verts.append((cx + px_ * ww, cy + py_ * ww, cz))
        for s in range(SEG):
            b = base + s * 2
            faces.append((b, b + 1, b + 3, b + 2))
    for ix in (-1, 0, 1):
        for iy in (-1, 0, 1):
            ob = mesh_object('blades', verts, faces, material=gmat)
            ob.location = (ix * T, iy * T, 0)
    # a few clover-like broad leaves and tiny daisies would not tile well: keep it pure grass
    set_camera(T)
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.cycles.samples = 96
    render_pair(os.path.join(out, 'grass'), normal=False)
    sc.render.film_transparent = True


# ----------------------------------------------------------------------------
# koi
# ----------------------------------------------------------------------------
def render_koi(out):
    """Koi seen from above, lying along +Y (head up).  The game bends the
    sprite itself to make it swim."""
    sc = bpy.context.scene
    kinds = [((1.0, 0.30, 0.02), (0.95, 0.93, 0.88), 3.0, 0.52),      # orange on white
             ((0.95, 0.93, 0.88), (0.9, 0.12, 0.02), 2.2, 0.46),      # white with red
             ((1.0, 0.55, 0.05), (1.0, 0.42, 0.03), 2.0, 0.5),        # gold
             ((0.03, 0.03, 0.035), (0.95, 0.35, 0.03), 2.6, 0.5)]     # black and orange
    sc.render.resolution_x = 192; sc.render.resolution_y = 512
    cam = sc.camera
    for i, (c1, c2, scale, thr) in enumerate(kinds):
        clear_objects()
        mat, nt, bsdf = principled('koi%d' % i)
        N, L = nt.nodes, nt.links
        tc = N.new('ShaderNodeTexCoord')
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 1.5
        mp = N.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (i * 3.1, i * 1.7, 0)
        L.new(tc.outputs['Object'], mp.inputs[0]); L.new(mp.outputs[0], nz.inputs['Vector'])
        mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = thr; mr.inputs['From Max'].default_value = thr + 0.03
        L.new(nz.outputs['Fac'], mr.inputs['Value'])
        mix = N.new('ShaderNodeMixRGB'); mix.inputs['Color1'].default_value = (*c1, 1); mix.inputs['Color2'].default_value = (*c2, 1)
        L.new(mr.outputs[0], mix.inputs['Fac']); L.new(mix.outputs[0], bsdf.inputs['Base Color'])
        set_input(bsdf, 'Roughness', 0.3)
        fmat, fnt, fb = principled('fin%d' % i)
        set_input(fb, 'Base Color', (*[0.5 * a + 0.5 * b for a, b in zip(c1, c2)], 1)); set_input(fb, 'Roughness', 0.5)
        set_input(fb, 'Alpha', 0.62)
        # body: lofted spindle
        M, K = 40, 16
        verts, faces = [], []
        for m in range(M):
            t = (m + 0.5) / M
            w = 0.21 * math.sin(math.pi * t ** 0.62) ** 0.9 * (1 - 0.55 * t ** 2.2) + 0.012
            hgt = w * 0.95
            y = 1.0 - 1.75 * t
            for k in range(K):
                a = 2 * math.pi * k / K
                verts.append((w * math.cos(a), y, hgt * math.sin(a)))
        for m in range(M - 1):
            for k in range(K):
                a, b = m * K + k, m * K + (k + 1) % K
                faces.append((a, b, b + K, a + K))
        body = mesh_object('koi', verts, faces, material=mat)
        add_subsurf(body, 1)
        # fins: tail, two pectorals, dorsal ridge
        def fin(points, z=0.0):
            f = mesh_object('fin', [(x, y, z) for x, y in points], [tuple(range(len(points)))], material=fmat)
            return f
        fin([(0, -0.70), (0.20, -1.06), (0.10, -1.02), (0, -0.90), (-0.10, -1.02), (-0.20, -1.06)])
        fin([(0.16, 0.52), (0.40, 0.30), (0.36, 0.20), (0.18, 0.36)], -0.03)
        fin([(-0.16, 0.52), (-0.40, 0.30), (-0.36, 0.20), (-0.18, 0.36)], -0.03)
        fin([(0.10, -0.18), (0.22, -0.34), (0.10, -0.32)], -0.03)
        fin([(-0.10, -0.18), (-0.22, -0.34), (-0.10, -0.32)], -0.03)
        cam.data.ortho_scale = 2.4
        cam.location = (0, -0.06, 20)
        render_pair(os.path.join(out, 'koi_%d' % i), normal=False)
    sc.render.resolution_x = sc.render.resolution_y = 384


# ----------------------------------------------------------------------------
# dragonfly
# ----------------------------------------------------------------------------
def render_dragonfly(out):
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = 256
    kinds = [(0.02, 0.35, 0.9), (0.85, 0.08, 0.03)]
    for i, col in enumerate(kinds):
        for wing_state in (0, 1):
            clear_objects()
            mat, nt, bsdf = principled('df')
            set_input(bsdf, 'Base Color', (*col, 1)); set_input(bsdf, 'Roughness', 0.25); set_input(bsdf, 'Metallic', 0.6)
            wmat, wnt, wb = principled('wing')
            set_input(wb, 'Base Color', (0.85, 0.92, 1.0, 1)); set_input(wb, 'Roughness', 0.15)
            set_input(wb, 'Alpha', 0.30 if wing_state == 0 else 0.14)
            # abdomen, thorax, head
            for (y0, y1, r) in [(-0.95, -0.05, 0.035), (-0.08, 0.22, 0.085), (0.22, 0.36, 0.075)]:
                bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=1.0, location=(0, (y0 + y1) / 2, 0))
                o = bpy.context.active_object
                o.scale = (r, (y1 - y0) / 2, r)
                bpy.ops.object.shade_smooth(); o.data.materials.append(mat)
            # two pairs of wings (blurred into a wider fan in the second state)
            def wing(sign, y, length, width, sweep):
                pts = []
                for k in range(15):
                    t = k / 14
                    a = math.pi * t
                    pts.append((sign * (0.05 + length * (0.5 - 0.5 * math.cos(a))), y + width * math.sin(a) * (0.6 + 0.4 * t) + sweep * t))
                for k in range(14, -1, -1):
                    t = k / 14
                    a = math.pi * t
                    pts.append((sign * (0.05 + length * (0.5 - 0.5 * math.cos(a))), y - width * 0.45 * math.sin(a) + sweep * t))
                mesh_object('wing', [(x, yy, 0.05) for x, yy in pts], [tuple(range(len(pts)))], smooth=False, material=wmat)
            spread = 1.0 if wing_state == 0 else 1.9
            for s in (-1, 1):
                wing(s, 0.14, 0.82, 0.085 * spread, 0.10)
                wing(s, 0.00, 0.78, 0.095 * spread, -0.12)
            set_camera(2.1, 0, -0.25)
            render_pair(os.path.join(out, 'dragonfly_%d_%d' % (i, wing_state)), normal=False)
    sc.render.resolution_x = sc.render.resolution_y = 384


# ----------------------------------------------------------------------------
def main():
    args = script_args()
    out = args[0]
    what = args[1:] or ['pads', 'flowers', 'rocks', 'grass', 'koi', 'dragonfly']
    os.makedirs(out, exist_ok=True)
    sc = reset_scene(samples=96, res=512)
    if 'pads' in what:
        sc.render.resolution_x = sc.render.resolution_y = 512
        render_pads(out)
    if 'flowers' in what:
        sc.render.resolution_x = sc.render.resolution_y = 320
        render_flowers(out)
    if 'rocks' in what:
        sc.render.resolution_x = sc.render.resolution_y = 256
        render_rocks(out)
    if 'koi' in what:
        render_koi(out)
    if 'dragonfly' in what:
        render_dragonfly(out)
    if 'grass' in what:
        render_grass(out)


main()
