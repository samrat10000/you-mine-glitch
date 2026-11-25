#!/usr/bin/env python3
"""qa_frames.py: the evidence step of the motion2d QA loop.

  python qa_frames.py <frames_dir_or_mp4> [--ref locked.png] [--crops crops.json] [--n 12] [--out qa]

Writes <out>/contact.jpg (n evenly spaced frames, numbered), <out>/crop_<name>_<frame>.png (full-size
crops), <out>/stats.json, and prints a PASS/FAIL table:
  - mean / p50 / p95 luminance and mean saturation per frame (and averaged)
  - delta vs --ref (must be within +-10% mean and p95 unless the shot card states another target)
  - p95 >= 0.78 warning for sun-facing shots (--sun)
  - black/NaN-like frames (mean < 0.02), duplicate consecutive frames (frozen motion), frame-count
crops.json: {"hand_L": [x, y, w, h], ...} in full-res pixels, or {"hand_L": {"48": [x,y,w,h], ...}} per frame
(build scripts should write these into meta.json from projected bone positions; pass meta.json directly,
its "crops" key is used).
Open contact.jpg and every crop afterwards and DESCRIBE them; numbers alone never pass a gate.
"""
import argparse, json, os, subprocess, sys, tempfile, glob
import numpy as np
from PIL import Image, ImageDraw


def load_frames(src):
    if os.path.isdir(src):
        fs = sorted(glob.glob(os.path.join(src, '*.png')) + glob.glob(os.path.join(src, '*.jpg')))
        return fs, None
    tmp = tempfile.mkdtemp(prefix='qaf_')
    subprocess.run(['ffmpeg', '-v', 'error', '-i', src, os.path.join(tmp, '%03d.png')], check=True)
    return sorted(glob.glob(os.path.join(tmp, '*.png'))), tmp


def stats(path):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    return dict(mean=float(lum.mean()), p50=float(np.percentile(lum, 50)), p95=float(np.percentile(lum, 95)),
                sat=float(sat.mean())), lum


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--ref'); ap.add_argument('--crops'); ap.add_argument('--n', type=int, default=12)
    ap.add_argument('--out', default='qa'); ap.add_argument('--sun', action='store_true'); ap.add_argument('--tol', type=float, default=0.10)
    a = ap.parse_args()
    frames, tmp = load_frames(a.src)
    if not frames:
        sys.exit('no frames found')
    os.makedirs(a.out, exist_ok=True)
    idx = sorted(set(int(round(i)) for i in np.linspace(0, len(frames) - 1, min(a.n, len(frames)))))
    res, prev, frozen, rows = {}, None, [], []
    for i, f in enumerate(frames):
        if i not in idx and not a.crops:
            # cheap frozen check on every frame
            pass
        s, lum = stats(f)
        if prev is not None and prev.shape == lum.shape and np.abs(prev - lum).mean() < 1e-4:
            frozen.append(i + 1)
        prev = lum
        if i in idx:
            res[os.path.basename(f)] = s
    # contact sheet
    ims = [Image.open(frames[i]).convert('RGB') for i in idx]
    th = 480; ims = [im.resize((int(im.width * th / im.height), th)) for im in ims]
    cols = min(6, len(ims)); rws = (len(ims) + cols - 1) // cols; w = ims[0].width
    sheet = Image.new('RGB', (cols * w, rws * th), (0, 0, 0)); d = ImageDraw.Draw(sheet)
    for k, (i, im) in enumerate(zip(idx, ims)):
        x, y = (k % cols) * w, (k // cols) * th; sheet.paste(im, (x, y)); d.text((x + 6, y + 6), f'{i + 1:03d}', fill=(255, 255, 0))
    sheet.save(os.path.join(a.out, 'contact.jpg'), quality=88)
    # crops
    if a.crops:
        cj = json.load(open(a.crops)); cj = cj.get('crops', cj)
        for name, spec in cj.items():
            items = spec.items() if isinstance(spec, dict) else [(str(idx[len(idx) // 2] + 1), spec)]
            for fr, (x, y, w_, h_) in items:
                fi = int(fr) - 1
                if 0 <= fi < len(frames):
                    Image.open(frames[fi]).crop((x, y, x + w_, y + h_)).save(os.path.join(a.out, f'crop_{name}_{int(fr):03d}.png'))
    avg = {k: float(np.mean([v[k] for v in res.values()])) for k in ('mean', 'p50', 'p95', 'sat')}
    report = dict(frames=len(frames), sampled=res, average=avg, frozen_frames=frozen)
    checks = []
    if a.ref:
        r, _ = stats(a.ref); report['ref'] = r
        for k in ('mean', 'p95'):
            dv = (avg[k] - r[k]) / max(r[k], 1e-4)
            checks.append((f'{k} vs ref {r[k]:.3f}', f'{avg[k]:.3f} ({dv:+.0%})', abs(dv) <= a.tol))
    if a.sun:
        checks.append(('p95 >= 0.78 (sun shot)', f"{avg['p95']:.3f}", avg['p95'] >= 0.78))
    dark = [k for k, v in res.items() if v['mean'] < 0.02]
    checks.append(('no black frames', ','.join(dark) or 'none', not dark))
    checks.append(('no frozen consecutive frames', f'{len(frozen)} frozen', len(frozen) <= len(frames) // 2))
    report['checks'] = [dict(check=c, value=v, ok=ok) for c, v, ok in checks]
    json.dump(report, open(os.path.join(a.out, 'stats.json'), 'w'), indent=1)
    print(f"frames {len(frames)} | avg mean {avg['mean']:.3f} p95 {avg['p95']:.3f} sat {avg['sat']:.3f}")
    for c, v, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {c}: {v}")
    print(f"wrote {a.out}/contact.jpg, stats.json" + (', crops' if a.crops else '') + "  -> now OPEN and DESCRIBE them")
    if frozen and len(frozen) > len(frames) // 2:
        print('note: characters on twos give ~half duplicate frames only if the camera is also held; a moving camera should give none')


if __name__ == '__main__':
    main()
