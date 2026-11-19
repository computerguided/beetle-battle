#!/usr/bin/env python3
"""Packs the Blender renders into the texture atlases used by the game.

    python3 lily_pond/tools/pack_assets.py RENDER_DIR [RENDER_DIR ...]

Writes lily_pond/assets/*.webp and lily_pond/assets/atlas.json.
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets')
FLAT = (128, 128, 255)


def find(name, dirs):
    for d in dirs:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def load(name, dirs):
    return Image.open(find(name, dirs)).convert('RGBA')


def flatten_normal(img):
    """Normal maps become opaque: outside the sprite they fade to 'straight up'."""
    bg = Image.new('RGBA', img.size, FLAT + (255,))
    bg.alpha_composite(img)
    return bg.convert('RGB')


def save(img, name, quality=90):
    path = os.path.join(OUT, name)
    if img.mode == 'RGBA':
        img.save(path, 'WEBP', quality=quality, method=6, exact=False, alpha_quality=95)
    else:
        img.save(path, 'WEBP', quality=quality, method=6)
    print('%-16s %5dx%-5d %7.0f kB' % (name, img.width, img.height, os.path.getsize(path) / 1024))


def main():
    dirs = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    meta = {}

    # ---- frogs: one grid, three images (red, blue, normals) ----
    frames = open(find('frog_frames.txt', dirs)).read().split()
    cell = load('frog_red_%s.png' % frames[0], dirs).width
    cols = 5
    rows = (len(frames) + cols - 1) // cols
    sheets = {k: Image.new('RGBA', (cols * cell, rows * cell), (0, 0, 0, 0)) for k in ('red', 'blue')}
    nsheet = Image.new('RGB', (cols * cell, rows * cell), FLAT)
    meta['frog'] = {'size': [cols * cell, rows * cell], 'cell': cell, 'frames': {},
                    'world': 2.2, 'anchor': [0.5, 0.5 + 0.42 / 2.2]}
    for i, f in enumerate(frames):
        x, y = (i % cols) * cell, (i // cols) * cell
        for k in sheets:
            sheets[k].paste(load('frog_%s_%s.png' % (k, f), dirs), (x, y))
        nsheet.paste(flatten_normal(load('frog_red_%s_n.png' % f, dirs)), (x, y))
        meta['frog']['frames'][f] = [x, y, cell, cell]
    save(sheets['red'], 'frog_red.webp', 92)
    save(sheets['blue'], 'frog_blue.webp', 92)
    save(nsheet, 'frog_n.webp', 90)

    # ---- lily pads ----
    n = 6
    cell = load('pad_0.png', dirs).width
    sheet = Image.new('RGBA', (3 * cell, 2 * cell), (0, 0, 0, 0))
    nsheet = Image.new('RGB', (3 * cell, 2 * cell), FLAT)
    meta['pad'] = {'size': [3 * cell, 2 * cell], 'rects': [], 'world': 2.2}
    for i in range(n):
        x, y = (i % 3) * cell, (i // 3) * cell
        sheet.paste(load('pad_%d.png' % i, dirs), (x, y))
        nsheet.paste(flatten_normal(load('pad_%d_n.png' % i, dirs)), (x, y))
        meta['pad']['rects'].append([x, y, cell, cell])
    save(sheet, 'pad.webp', 90)
    save(nsheet, 'pad_n.webp', 88)

    # ---- props: rocks, flowers, dragonflies, koi ----
    W, H = 2048, 1088
    sheet = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    nsheet = Image.new('RGB', (W, H), FLAT)
    meta['props'] = {'size': [W, H], 'rock': [], 'flower': [], 'dragonfly': [], 'koi': []}
    for i in range(8):
        im = load('rock_%d.png' % i, dirs)
        sheet.paste(im, (i * 256, 0)); nsheet.paste(flatten_normal(load('rock_%d_n.png' % i, dirs)), (i * 256, 0))
        meta['props']['rock'].append([i * 256, 0, 256, 256])
    for i in range(3):
        im = load('flower_%d.png' % i, dirs)
        sheet.paste(im, (i * 320, 256)); nsheet.paste(flatten_normal(load('flower_%d_n.png' % i, dirs)), (i * 320, 256))
        meta['props']['flower'].append([i * 320, 256, 320, 320])
    k = 0
    for i in range(2):
        pair = []
        for s in range(2):
            sheet.paste(load('dragonfly_%d_%d.png' % (i, s), dirs), (960 + k * 256, 256))
            pair.append([960 + k * 256, 256, 256, 256]); k += 1
        meta['props']['dragonfly'].append(pair)
    for i in range(4):
        sheet.paste(load('koi_%d.png' % i, dirs), (i * 192, 576))
        meta['props']['koi'].append([i * 192, 576, 192, 512])
    save(sheet, 'props.webp', 90)
    save(nsheet, 'props_n.webp', 85)

    # ---- grass ----
    save(Image.open(find('grass.png', dirs)).convert('RGB'), 'grass.webp', 82)

    with open(os.path.join(OUT, 'atlas.json'), 'w') as fh:
        json.dump(meta, fh, separators=(',', ':'))
    print('atlas.json written')


main()
