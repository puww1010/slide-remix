#!/usr/bin/env python3
"""Zoom into a screenshot for mode A (slide forensics): crop a region and upscale it, or cut the image into tiles.

usage: python3 crop.py IMG --box x0,y0,x1,y1 [--scale 3] [--out zoom.png]
       python3 crop.py IMG --grid 3x3 [--scale 2] [--out-dir tiles/]
Coordinates are pixels of the original image (print them with: python3 crop.py IMG --info).
Then open the output PNG(s) with the Read tool and look for evidence (line jumps, fonts, footer, icons, alignment).
"""
import argparse, os, sys

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('img')
    ap.add_argument('--box'); ap.add_argument('--grid'); ap.add_argument('--info', action='store_true')
    ap.add_argument('--scale', type=float, default=3); ap.add_argument('--out', default='zoom.png'); ap.add_argument('--out-dir', default='tiles')
    a = ap.parse_args()
    try:
        from PIL import Image
    except ImportError:
        sys.exit('[FAIL] Pillow is not installed: pip install Pillow')
    try:
        im = Image.open(a.img); im.load()
    except FileNotFoundError:
        sys.exit(f'[FAIL] image not found: {a.img}')
    except Exception as e:
        sys.exit(f'[FAIL] cannot open {a.img} as an image ({type(e).__name__})')
    W, H = im.size
    if a.info or not (a.box or a.grid):
        print(f'[info] {a.img}: {W} x {H} px'); return
    up = lambda r: r.resize((max(1, int(r.width * a.scale)), max(1, int(r.height * a.scale))), Image.LANCZOS)
    if a.box:
        try:
            x0, y0, x1, y1 = [int(float(v)) for v in a.box.split(',')]
        except ValueError:
            sys.exit('[FAIL] --box must be x0,y0,x1,y1 (pixels)')
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        if x1 <= x0 or y1 <= y0: sys.exit(f'[FAIL] --box is empty after clipping to the image ({W} x {H})')
        up(im.crop((x0, y0, x1, y1))).save(a.out); print('[crop]', a.out)
    if a.grid:
        try:
            c, r = [int(v) for v in a.grid.lower().split('x')]
        except ValueError:
            sys.exit('[FAIL] --grid must look like 3x3')
        os.makedirs(a.out_dir, exist_ok=True)
        for j in range(r):
            for i in range(c):
                box = (W * i // c, H * j // r, W * (i + 1) // c, H * (j + 1) // r)
                p = os.path.join(a.out_dir, f'tile_r{j + 1}c{i + 1}.png'); up(im.crop(box)).save(p); print('[tile]', p, box)

if __name__ == '__main__':
    main()
