#!/usr/bin/env python3
"""Builds the single-file game: ../lily_pond.html

Everything (scripts, textures, sounds) is embedded, so the page can be opened
straight from disk or through htmlpreview, like the other HTML versions.

    python3 lily_pond/build.py
"""
import base64, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
ASSETS = os.path.join(HERE, 'assets')
OUT = os.path.join(HERE, '..', 'lily_pond.html')
MIME = {'.webp': 'image/webp', '.mp3': 'audio/mpeg'}


def data_uri(path):
    ext = os.path.splitext(path)[1]
    with open(path, 'rb') as fh:
        return 'data:%s;base64,%s' % (MIME[ext], base64.b64encode(fh.read()).decode())


def main():
    html = open(os.path.join(SRC, 'index.html'), encoding='utf-8').read()
    assets = {}
    for name in sorted(os.listdir(ASSETS)):
        base, ext = os.path.splitext(name)
        if ext in MIME:
            assets[base] = data_uri(os.path.join(ASSETS, name))
    atlas = json.load(open(os.path.join(ASSETS, 'atlas.json')))
    blob = 'const ASSETS=%s;\nconst ATLAS=%s;' % (json.dumps(assets), json.dumps(atlas, separators=(',', ':')))
    html = html.replace('/*__ASSETS__*/', blob)

    def inline(match):
        code = open(os.path.join(SRC, match.group(1)), encoding='utf-8').read()
        return '<script>\n%s\n</script>' % code.replace('</script', '<\\/script')
    html = re.sub(r'<script src="([^"]+)"></script>', inline, html)
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(html)
    print('wrote %s (%.2f MB)' % (os.path.normpath(OUT), os.path.getsize(OUT) / 1e6))


if __name__ == '__main__':
    main()
