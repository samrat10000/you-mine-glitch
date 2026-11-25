"""Ep1 v2 sound: Flow piano take + ElevenLabs lines + real chime (VSCO-2 marimba/glock) + real SFX, blended:
music thins under each line (sidechain duck ~8 dB), swells back in the gaps, never stops.
usage: python mix_v2.py <flow_take.mp3> <audio_dir with N1,N2,S1,P1,S2 takes> <out.wav>
Needs: VSCO-2 marimba+glock at ./vsco (git sparse clone sgossner/VSCO-2-CE), SFX in ./snd (of.py downloads)."""
import sys, os, glob
from music import *
import music
music.V = os.environ.get('VSCO', './vsco')
V = music.V

DUR = 21.0
LINES = [('N1', .6, 'narr'), ('N2', 7.4, 'narr'), ('S1', 11.0, 'whisper'), ('P1', 12.7, 'pa'), ('S2', 16.9, 'mirror')]
CHIME = [(5.55, 66), (6.05, 70), (6.55, 73)]
FOURTH = 18.4
BLACK = 19.1


def pick_take(d, key):
    fs = sorted(glob.glob(os.path.join(d, f'{key}*')))
    if not fs:
        raise SystemExit(f'missing voice line {key} in {d}')
    return fs[0]   # takeA by default; rename to choose another


def trim(x, thr_db=-45):
    m = np.abs(x).mean(1)
    win = int(.01 * SR)
    e = np.convolve(m, np.ones(win) / win, 'same')
    idx = np.where(e > 10 ** (thr_db / 20))[0]
    if len(idx) == 0:
        return x
    a, b = max(0, idx[0] - int(.03 * SR)), min(len(x), idx[-1] + int(.12 * SR))
    return x[a:b]


def norm_rms(x, db):
    r = np.sqrt((x ** 2).mean()) + 1e-9
    return x * (10 ** (db / 20) / r)


def voice(kind, x):
    x = hp(trim(x), 70)
    if kind == 'narr':      # deep, close, warm: tiny low lift, no room
        x = x + lp(x, 180) * .35
        return norm_rms(x, -20)
    if kind == 'whisper':
        return norm_rms(reverb(x, .6, .12, 21), -25)
    if kind == 'pa':        # the town loudspeaker
        return norm_rms(pa_speaker(x), -23)
    if kind == 'mirror':    # night-Sam: closer, drier, a hair lower
        x = shift(x, -0.7)
        x = x + lp(x, 220) * .25
        return norm_rms(x, -21)
    return norm_rms(x, -21)


def main(flow, adir, out):
    n = int(DUR * SR)
    vo = Mix(DUR)
    spans = []
    for key, t, kind in LINES:
        x = voice(kind, load(pick_take(adir, key)))
        vo.add(x, t)
        spans.append((key, t, t + len(x) / SR))
    for (a, b), (c, d) in zip([s[1:] for s in spans], [s[1:] for s in spans[1:]]):
        if b > c - .25:
            print(f'WARNING: line ending {b:.2f}s runs into next line at {c:.2f}s')
    print('lines:', [(k, round(a, 2), round(b, 2)) for k, a, b in spans])
    # music: Flow take, trimmed/faded to the reel
    mu = load(flow)[:n]
    if len(mu) < n:
        mu = np.concatenate([mu, np.zeros((n - len(mu), 2), np.float32)])
    mu = fade(mu, .05, 1.8)
    # sidechain duck from the voice envelope (attack 60 ms, release 450 ms), -8 dB
    env = np.abs(vo.y).mean(1)
    k = int(.02 * SR)
    env = np.convolve(env, np.ones(k) / k, 'same')
    on = (env > 10 ** (-42 / 20)).astype(np.float32)
    g = np.ones(n, np.float32); cur = 1.0
    a_att, a_rel = np.exp(-1 / (.06 * SR)), np.exp(-1 / (.45 * SR))
    tgt_lo = 10 ** (-8 / 20)
    for i in range(n):
        tgt = tgt_lo if on[i] else 1.0
        a = a_att if tgt < cur else a_rel
        cur = tgt + (cur - tgt) * a
        g[i] = cur
    mu = mu * g[:, None]
    # chime (only bright note), real samples
    MAR = named_bank(f'{V}/Percussion/Marimba/*.wav')
    GLK = named_bank(f'{V}/Percussion/Glock/*.wav')
    ch = Mix(DUR)
    for t, m in CHIME:
        x = addv(note(MAR, m, .6, att=.002, rel=1.2) * .9, note(GLK, m + 12, .4, att=.002, rel=1.0) * .35)
        ch.add(pa_speaker(x), t)
    x = addv(note(MAR, 78, .8, att=.002, rel=1.6) * .9, note(GLK, 90, .6, att=.002, rel=1.4) * .4)
    ch.add(lp(x, 9000), FOURTH, 1.2)
    chime = norm_rms(reverb(ch.y, 2.5, .25, 13), -24)
    # music dips just before the chime and the 4th note so they read clearly, then returns
    mu *= automation(n, [(0, 1), (5.3, 1), (5.5, .55), (7.2, .55), (7.5, 1), (18.1, 1), (18.35, .45), (18.9, 1), (DUR, 1)])
    # SFX bed (real recordings): wind in wires + distant crows; dies when the town freezes
    sfx = Mix(DUR)
    try:
        w = hp(lp(load(sorted(glob.glob('snd/wires/4_*'))[0])[30 * SR:52 * SR], 3200), 60)
        w = norm_rms(w, -34)[:n]
        sfx.add(w * automation(len(w), [(0, 0), (.3, 1), (12.0, 1), (13.0, .6), (16.5, .5), (17.5, 0), (DUR, 0)]), 0)
        cr = load(sorted(glob.glob('snd/crows/0_*'))[0])
        sfx.add(reverb(lp(shift(cr[int(.7 * SR):int(2.1 * SR)], -3), 2200), 2.2, .35, 7), 1.6, .07)
        fl = load(sorted(glob.glob('snd/crows/5_*'))[0])[10 * SR:13 * SR]
        sfx.add(fade(norm_rms(hp(fl, 250), -28), .15, 1.2), 5.6)
    except Exception as e:
        print('sfx skipped:', e)
    mix = mu * .95 + vo.y + chime + sfx.y
    mix *= automation(n, [(0, 1), (BLACK + 1.2, 1), (DUR, .0)])
    mix = mix / (np.abs(mix).max() + 1e-9) * .9
    import wave
    y16 = (np.clip(mix, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(y16.tobytes())
    print('wrote', out)


if __name__ == '__main__':
    main(*sys.argv[1:4])
