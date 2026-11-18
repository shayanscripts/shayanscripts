"""Builds the retro-arcade SVGs for the GitHub profile README.

Black + neon green, a hand-made 5x7 pixel font, glow, scanlines, a starfield
and a little space battle (ships trading lasers, explosions, spinning
asteroids, comets) flying through every panel. Pulls live numbers (repos,
stars, followers, languages) from the public GitHub API, so the daily
workflow keeps the board current.

    python scripts/build_svgs.py            # uses GITHUB_TOKEN if set

Standard library only. Edit PROFILE / IMPORTANCE / WORLDS / ACHIEVEMENTS below.
"""

import json
import math
import os
import random
import sys
import urllib.request
import zlib
from xml.sax.saxutils import escape

USER = os.environ.get("PROFILE_USER", "shayanscripts")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

NEON = "#39ff14"
MID = "#2fd010"
DIM = "#1b7a0e"
DARK = "#0b2a06"
BG = "#000000"

PROFILE = {
    "name": "RANA SHAYAN",
    "age": 18,
    "bio": "BUILDING AI STUFF AND BREAKING THINGS IN THE PROCESS",
}

# High scores are ranked by importance (this order), not by stars.
# Repos missing from the list follow, most-starred first.
IMPORTANCE = [
    "watchword",
    "GATE---General-Acceleration-Threshold-Examiner",
    "selfguard",
    "injection-holdout",
    "repolens-ai",
    "redshift",
    "noctilith",
    "github-guard",
]

# world -> repos (in order). Repos not listed show up under "BONUS STAGES".
WORLDS = [
    ("WORLD 1: AI SECURITY", ["watchword", "GATE---General-Acceleration-Threshold-Examiner", "selfguard", "injection-holdout"]),
    ("WORLD 2: DEEP SPACE", ["redshift", "noctilith"]),
    ("WORLD 3: DEV TOOLS", ["github-guard", "repolens-ai"]),
]
SHORT_NAME = {"GATE---General-Acceleration-Threshold-Examiner": "GATE"}
TAGLINE = {
    "watchword": "Prompt-injection preventer for LLM apps. No training, no extra calls. Sealed test: 3/3 PASS.",
    "GATE---General-Acceleration-Threshold-Examiner": "Zero-modification prompt-injection detector using entropic acceleration signals. Benchmarked on SEP.",
    "selfguard": "Post-generation behavioural-drift signals for catching prompt injection.",
    "injection-holdout": "Sealed, pre-registered prompt-injection test set with deterministic build scripts.",
    "redshift": "Fly NASA's SPHEREx around a photoreal, full-scale Earth in the browser.",
    "noctilith": "Flip through every SPHEREx image of a sky patch to spot moving or changing objects.",
    "github-guard": "Dependency-free Git pre-commit scanner that catches secrets before they ship.",
    "repolens-ai": "AI explainer for GitHub repos: implementation guides, reading paths, architecture maps.",
}
ACHIEVEMENTS = [
    "SEALED TEST CLEARED: WATCHWORD 3/3",
    "PRE-REGISTERED A BENCHMARK",
    "FLEW A SPACE TELESCOPE (IN A BROWSER)",
]
LANG_SHORT = {"Python": "PYTHON", "JavaScript": "JS", "TypeScript": "TS", None: "WEB"}

# --------------------------------------------------------------------------
# 5x7 pixel font ('@' is a star)
# --------------------------------------------------------------------------
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000"] * 7,
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    ">": ["01000", "00100", "00010", "00001", "00010", "00100", "01000"],
    "*": ["00000", "10101", "01110", "11111", "01110", "10101", "00000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "@": ["00100", "00100", "11111", "01110", "01110", "11011", "10001"],
}


def text_width(s, scale):
    return max(len(s) * 6 - 1, 0) * scale


def pixel_text(s, x, y, scale, fill=NEON, extra=""):
    """Pixel-font text as merged rects. (x, y) is the top-left corner."""
    rects = []
    for i, ch in enumerate(s.upper()):
        glyph = FONT.get(ch, FONT["?"])
        gx = x + i * 6 * scale
        for r, row in enumerate(glyph):
            c = 0
            while c < 5:
                if row[c] == "1":
                    start = c
                    while c < 5 and row[c] == "1":
                        c += 1
                    rects.append(f'<rect x="{gx + start * scale:g}" y="{y + r * scale:g}" width="{(c - start) * scale:g}" height="{scale:g}"/>')
                else:
                    c += 1
    return f'<g fill="{fill}" {extra}>{"".join(rects)}</g>'


def centered(s, cx, y, scale, fill=NEON, extra=""):
    return pixel_text(s, cx - text_width(s, scale) / 2, y, scale, fill, extra)


def sprite(rows, x, y, scale, colors=None, extra=""):
    """Bitmap sprite; each digit picks a colour from `colors` (0 = empty)."""
    colors = colors or {"1": NEON}
    rects = []
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if v != "0" and v in colors:
                rects.append(f'<rect x="{x + c * scale:g}" y="{y + r * scale:g}" width="{scale:g}" height="{scale:g}" fill="{colors[v]}"/>')
    return f'<g {extra}>{"".join(rects)}</g>'


# Original pixel sprites ------------------------------------------------------
# 1 = bright, 2 = body, 3 = shade, 4 = glow (cockpit / eye)
HERO = [            # our fighter, nose to the right (16 x 11)
    "0110000000000000",
    "0121100000000000",
    "0122211110000000",
    "0012222221110000",
    "1112233322221100",
    "1222334433222211",
    "1112233322221100",
    "0012222221110000",
    "0122211110000000",
    "0121100000000000",
    "0110000000000000",
]
HERO_PAL = {"1": NEON, "2": MID, "3": DIM, "4": "#c8ffb0"}
ENEMY = [           # raider, nose to the left (14 x 9)
    "00000011110000",
    "00001122221011",
    "00112223322110",
    "01222233332221",
    "12224433332221",
    "01222233332221",
    "00112223322110",
    "00001122221011",
    "00000011110000",
]
ENEMY_PAL = {"1": MID, "2": DIM, "3": DARK, "4": NEON}


def hero_sprite(s):
    """Fighter (16 x 11 cells) with a flickering engine flame; (0, 0) is its top-left."""
    return (sprite(["011", "111", "011"], -3 * s, 4 * s, s, {"1": "#c8ffb0"}, 'class="fa"')
            + sprite(["0011", "1111", "0011"], -4 * s, 4 * s, s, {"1": MID}, 'class="fb"')
            + sprite(HERO, 0, 0, s, HERO_PAL, 'filter="url(#glow)"'))


def enemy_sprite(s):
    """Raider (14 x 9 cells), exhaust flickering behind it on the right."""
    return (sprite(["110", "111", "110"], 14 * s, 3 * s, s, {"1": DIM}, 'class="fa"')
            + sprite(["1100", "1111", "1100"], 14 * s, 3 * s, s, {"1": DARK}, 'class="fb"')
            + sprite(ENEMY, 0, 0, s, ENEMY_PAL))


ASTEROID = [
    "0022220000",
    "0211112200",
    "2111211120",
    "2111111112",
    "2121111112",
    "2111111212",
    "0211111120",
    "0022112200",
    "0000222000",
]
BURST = [
    "1000100010",
    "0100100100",
    "0010101000",
    "0001110000",
    "1111111111",
    "0001110000",
    "0010101000",
    "0100100100",
    "1000100010",
]

DEFS = f"""<defs>
  <filter id="glow" x="-20%" y="-60%" width="140%" height="220%">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="2" fill="#000" opacity="0.38"/>
  </pattern>
  <linearGradient id="tail" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0" stop-color="{NEON}" stop-opacity="0"/>
    <stop offset="1" stop-color="{NEON}" stop-opacity="0.9"/>
  </linearGradient>
</defs>
<style>
  .blink {{ animation: blink 1.1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  .tw {{ animation: tw 3s ease-in-out infinite; }}
  @keyframes tw {{ 0%,100% {{ opacity: .25; }} 50% {{ opacity: 1; }} }}
  .pulse {{ animation: pulse 2.4s ease-in-out infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity: .75; }} 50% {{ opacity: 1; }} }}
  .spin {{ transform-box: fill-box; transform-origin: center; animation: spin linear infinite; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  .bob {{ animation: bob 1.6s ease-in-out infinite; }}
  @keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(6px); }} }}
  .zapR {{ animation: zapR .8s linear infinite; }}
  @keyframes zapR {{ 0% {{ transform: translateX(0); opacity: 1; }} 85% {{ opacity: 1; }} 100% {{ transform: translateX(240px); opacity: 0; }} }}
  .zapL {{ animation: zapL 1.1s linear infinite; }}
  @keyframes zapL {{ 0% {{ transform: translateX(0); opacity: 1; }} 85% {{ opacity: 1; }} 100% {{ transform: translateX(-200px); opacity: 0; }} }}
  .fa {{ animation: fl .14s steps(1) infinite; }}
  .fb {{ animation: fl .14s steps(1) -.07s infinite; }}
  @keyframes fl {{ 50% {{ opacity: 0; }} }}
  .boom {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: boom steps(6) infinite; }}
  @keyframes boom {{ 0% {{ opacity: 0; transform: scale(.4); }} 4% {{ opacity: 1; transform: scale(.7); }}
                     12% {{ opacity: 1; transform: scale(1.4); }} 18%,100% {{ opacity: 0; transform: scale(1.6); }} }}
</style>"""


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}">\n<title>{escape(label)}</title>\n{DEFS}\n'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>\n{body}\n'
            f'<rect width="{w}" height="{h}" fill="url(#scan)" pointer-events="none"/>\n</svg>\n')


def frame(w, h, inset=6, r=14):
    return (f'<rect x="{inset}" y="{inset}" width="{w - 2 * inset}" height="{h - 2 * inset}" rx="{r}" '
            f'fill="none" stroke="{NEON}" stroke-width="3" filter="url(#glow)"/>'
            f'<rect x="{inset + 7}" y="{inset + 7}" width="{w - 2 * inset - 14}" height="{h - 2 * inset - 14}" rx="{max(r - 6, 2)}" '
            f'fill="none" stroke="{DIM}" stroke-width="1.5"/>')


def starfield(w, h, n, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(16, w - 16), rnd.uniform(16, h - 16)
        s = rnd.choice([2, 2, 2, 3, 4])
        delay = rnd.uniform(0, 3)
        cls = ' class="tw"' if rnd.random() < 0.6 else ""
        out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{s}" height="{s}" fill="{NEON if s > 2 else DIM}"{cls} style="animation-delay:{delay:.2f}s"/>')
    return "".join(out)


def space(w, h, seed, comets=2, asteroids=2, lanes=(), rocks=None, opacity=0.9, ship=3):
    """The moving background: comets, drifting asteroids and ship dogfights.

    `lanes` are the y centres (px) of empty bands the ships fly along, so they
    never cross text. `rocks` lists (top, bottom) bands for the asteroids.
    In each lane our fighter flies right firing; a raider flies in from the
    right, gets hit and explodes before they meet. Everything is clipped to
    the inside of the frame and loops forever.
    """
    rnd = random.Random(seed)
    span = w + 200
    css = [f"@keyframes cm{{0%{{transform:translateX(0);opacity:1}}30%{{transform:translateX({span + 300}px);opacity:1}}"
           f"30.1%,100%{{transform:translateX({span + 300}px);opacity:0}}}}",
           f"@keyframes goR{{from{{transform:translateX(0)}}to{{transform:translateX({span}px)}}}}",
           f"@keyframes goL{{from{{transform:translateX(0)}}to{{transform:translateX(-{span}px)}}}}"]
    out = []
    for _ in range(comets):
        y0 = rnd.uniform(-0.2, 0.5) * h
        ang = rnd.uniform(8, 24)
        cycle = rnd.uniform(9, 16)
        delay = rnd.uniform(-cycle, cycle * 0.6)
        out.append(f'<g transform="translate(-120,{y0:.0f}) rotate({ang:.1f})">'
                   f'<g style="opacity:0;animation:cm {cycle:.1f}s linear {delay:.1f}s infinite">'
                   f'<rect x="-90" y="-1.5" width="90" height="3" fill="url(#tail)"/>'
                   f'<rect x="-2" y="-3" width="6" height="6" fill="{NEON}" filter="url(#glow)"/></g></g>')
    bands = rocks or [(0.08 * h, 0.85 * h)]
    for _ in range(asteroids):
        top, bottom = rnd.choice(bands)
        fits = [s for s in (2, 3, 4) if 9 * s <= bottom - top] or [1]
        s = rnd.choice(fits)
        y = rnd.uniform(top, bottom - 9 * s)
        dur = rnd.uniform(22, 40) * w / 1000 + 6
        spin = f'class="spin" style="animation-duration:{rnd.uniform(5, 12):.1f}s"'
        out.append(f'<g style="animation:goL {dur:.1f}s linear {-rnd.uniform(0, dur):.1f}s infinite">'
                   f'<g transform="translate({w + 60},{y:.0f})">'
                   f'{sprite(ASTEROID, 0, 0, s, {"1": DARK, "2": DIM}, spin)}'
                   f'</g></g>')
    for i, yc in enumerate(lanes):
        top = yc - 5.5 * ship - 3                     # centre the ship, allowing for the 6 px bob
        etop = yc - 4.5 * ship - 3
        dur = rnd.uniform(9, 13) * max(w, 500) / 1000 + 3
        off = -rnd.uniform(0, dur)
        p = max(0.1, min(0.9, (w + 140 - 16 * ship - 140) / (2 * span)))
        pc = p * 100
        ex = w + 40 - p * span                        # raider's x when it is hit
        css.append(f"@keyframes ek{i}{{0%{{transform:translateX(0);opacity:1}}"
                   f"{pc:.2f}%{{transform:translateX(-{p * span:.0f}px);opacity:1}}"
                   f"{pc + 0.01:.2f}%{{transform:translateX(-{p * span:.0f}px);opacity:0}}"
                   f"100%{{transform:translateX(-{span}px);opacity:0}}}}")
        css.append(f"@keyframes bk{i}{{0%,{pc:.2f}%{{opacity:0;transform:scale(.5)}}"
                   f"{pc + 0.3:.2f}%{{opacity:1;transform:scale(.8)}}"
                   f"{pc + 3:.2f}%{{opacity:1;transform:scale(1.5)}}"
                   f"{pc + 6:.2f}%,100%{{opacity:0;transform:scale(1.7)}}}}")
        out.append(f'<g style="animation:goR {dur:.1f}s linear {off:.2f}s infinite"><g transform="translate(-120,{top:.0f})">'
                   f'<g class="bob">'
                   f'<rect x="{16 * ship}" y="{5 * ship}" width="{5 * ship}" height="{ship}" fill="{NEON}" class="zapR"/>'
                   f'<rect x="{16 * ship}" y="{5 * ship}" width="{5 * ship}" height="{ship}" fill="{NEON}" class="zapR" style="animation-delay:-.4s"/>'
                   f'{hero_sprite(ship)}</g></g></g>')
        out.append(f'<g style="animation:ek{i} {dur:.1f}s linear {off:.2f}s infinite"><g transform="translate({w + 40},{etop:.0f})">'
                   f'<g class="bob">'
                   f'<rect x="{-4 * ship}" y="{4 * ship}" width="{3 * ship}" height="{ship}" fill="{MID}" class="zapL"/>'
                   f'{enemy_sprite(ship)}</g></g></g>')
        boom = (f'style="transform-box:fill-box;transform-origin:center;opacity:0;'
                f'animation:bk{i} {dur:.1f}s linear {off:.2f}s infinite"')
        out.append(f'<g transform="translate({ex + 7 * ship - 15:.0f},{yc - 13.5:.0f})">'
                   f'{sprite(BURST, 0, 0, 3, {"1": NEON}, boom)}</g>')
    clip = f'<clipPath id="spc"><rect x="13" y="13" width="{w - 26}" height="{h - 26}" rx="8"/></clipPath>'
    return f'<defs>{clip}</defs><style>{"".join(css)}</style><g clip-path="url(#spc)" opacity="{opacity}">' + "".join(out) + "</g>"


def arena():
    """A little shoot-'em-up: scrolling stars, a raider wave, then a boss."""
    w, h, T = 1000, 230, 10.0
    lanes = [70, 118, 166]
    hs, es, bs = 4, 4, 6                     # hero / raider / boss pixel sizes
    hx = 100
    nose = hx + 16 * hs

    def pc(t):
        return t / T * 100

    def window(name, a, b):
        """Visible from time a to time b of each loop, hidden otherwise."""
        on = "0%" if a <= 0 else f"{pc(a):.3f}%"
        off = "" if b >= T else f"{pc(b) + 0.01:.3f}%,100%{{opacity:0}}"
        hidden = "" if a <= 0 else f"0%,{pc(a) - 0.01:.3f}%{{opacity:0}}"
        last = "100%" if b >= T else f"{pc(b):.3f}%"
        return f"@keyframes {name}{{{hidden}{on},{last}{{opacity:1}}{off}}}"

    css, b = [], [frame(w, h)]
    inner = []
    # parallax starfield: two layers scrolling left, drawn twice for a seamless loop
    rnd = random.Random(77)
    for layer, (n, size, col, dur) in enumerate([(40, 2, DIM, 22), (18, 3, NEON, 9)]):
        pts = [(rnd.uniform(0, w), rnd.uniform(16, h - 16)) for _ in range(n)]
        rects = "".join(f'<rect x="{x + dx:.0f}" y="{y:.0f}" width="{size}" height="{size}" fill="{col}"/>'
                        for x, y in pts for dx in (0, w))
        css.append(f"@keyframes sl{layer}{{from{{transform:translateX(0)}}to{{transform:translateX(-{w}px)}}}}")
        inner.append(f'<g style="animation:sl{layer} {dur}s linear infinite">{rects}</g>')

    # the fights: (lane, enter, kill, speed, size, points)
    fights = [(0, 0.2, 1.9, 250, es, 100), (2, 1.6, 3.6, 250, es, 100), (1, 3.2, 5.4, 250, es, 100),
              (1, 5.8, 8.6, 150, bs, 500)]
    # hero lines up with each target for the second before it dies
    stops = [(0.0, lanes[1])]
    for lane, _, tk, _, _, _ in fights:
        fire = tk - (2.0 if tk > 8 else 1.0)
        y = lanes[lane]
        if stops[-1][1] != y:
            stops.append((max(stops[-1][0], fire - 0.6), stops[-1][1]))
            stops.append((fire, y))
        stops.append((tk, y))
    stops.append((T, lanes[1]))
    css.append("@keyframes hy{" + "".join(f"{pc(t):.3f}%{{transform:translateY({y - 5.5 * hs - 3:.0f}px)}}" for t, y in stops) + "}")
    inner.append(f'<g transform="translate({hx},0)"><g style="animation:hy {T}s ease-in-out infinite">'
                 f'<g class="bob">{hero_sprite(hs)}</g></g></g>')

    score, score_times = 0, [(0.0, 0)]
    for i, (lane, te, tk, v, s, pts) in enumerate(fights):
        y = lanes[lane]
        top = y - 4.5 * s - 3
        xk = 1060 - v * (tk - te)                       # where it is when it dies
        ew = 14 * s
        # enemy flight
        css.append(f"@keyframes en{i}{{0%,{pc(te):.3f}%{{transform:translateX(1060px);opacity:0}}"
                   f"{pc(te) + 0.01:.3f}%{{transform:translateX(1060px);opacity:1}}"
                   f"{pc(tk):.3f}%{{transform:translateX({xk:.0f}px);opacity:1}}"
                   f"{pc(tk) + 0.01:.3f}%,100%{{transform:translateX({xk:.0f}px);opacity:0}}}}")
        fire = tk - (2.0 if s == bs else 1.0)
        css.append(window(f"fw{i}", fire, tk))
        # hits flash on the target's nose (and travel with it) while it takes fire
        blink = 'class="blink"'
        hits = (f'<g style="opacity:0;animation:fw{i} {T}s linear infinite" transform="translate({-2 * s},{4.5 * s - 3 * (2 if s == bs else 1.5):.0f})">'
                f'{sprite(BURST, 0, 0, 2 if s == bs else 1.5, {"1": "#c8ffb0"}, blink)}</g>')
        inner.append(f'<g style="animation:en{i} {T}s linear infinite"><g transform="translate(0,{top:.0f})">'
                     f'<g class="bob" style="animation-delay:-{i * 0.5:.1f}s">'
                     f'<rect x="{-4 * s}" y="{4 * s}" width="{3 * s}" height="{s}" fill="{MID}" class="zapL"/>'
                     f'{enemy_sprite(s)}{hits}</g></g></g>')
        # our laser stream: bolts reach the target's position at the start of
        # the firing window, so they always connect as it closes in
        x_start = 1060 - v * (fire - te)
        dist = x_start - nose + 10
        css.append(f"@keyframes zw{i}{{0%{{transform:translateX(0);opacity:1}}90%{{opacity:1}}100%{{transform:translateX({dist:.0f}px);opacity:0}}}}")
        bolts = "".join(f'<rect x="{nose}" y="{y - 2:.0f}" width="22" height="4" fill="{NEON}" '
                        f'style="animation:zw{i} .42s linear {-k * 0.14:.2f}s infinite"/>' for k in range(3))
        inner.append(f'<g style="opacity:0;animation:fw{i} {T}s linear infinite" filter="url(#glow)">'
                     f'{bolts}<rect x="{nose - 2}" y="{y - 5:.0f}" width="8" height="10" fill="#c8ffb0" class="blink"/></g>')
        # explosion: burst, flying debris and a score popup
        cx, cy = xk + ew / 2, y
        big = 2 if s == bs else 1
        css.append(f"@keyframes bx{i}{{0%,{pc(tk):.3f}%{{opacity:0;transform:scale(.4)}}{pc(tk) + 0.2:.3f}%{{opacity:1;transform:scale(.8)}}"
                   f"{pc(tk) + 4:.3f}%{{opacity:1;transform:scale(1.6)}}{pc(tk) + 7:.3f}%,100%{{opacity:0;transform:scale(1.9)}}}}")
        bw, bh = 10 * 4 * big, 9 * 4 * big
        burst_style = f'style="transform-box:fill-box;transform-origin:center;opacity:0;animation:bx{i} {T}s linear infinite"'
        inner.append(f'<g transform="translate({cx - bw / 2:.0f},{cy - bh / 2:.0f})">'
                     f'{sprite(BURST, 0, 0, 4 * big, {"1": NEON}, burst_style)}</g>')
        for d in range(10 * big):
            ang = d / (10 * big) * 6.283 + rnd.uniform(-0.3, 0.3)
            dist_d = rnd.uniform(40, 90) * big
            dx, dy = dist_d * math.cos(ang), dist_d * math.sin(ang)
            css.append(f"@keyframes db{i}_{d}{{0%,{pc(tk):.3f}%{{opacity:0;transform:translate(0,0)}}{pc(tk) + 0.2:.3f}%{{opacity:1;transform:translate(0,0)}}"
                       f"{pc(tk) + 8:.3f}%,100%{{opacity:0;transform:translate({dx:.0f}px,{dy:.0f}px)}}}}")
            size = rnd.choice([3, 4, 5])
            inner.append(f'<rect x="{cx:.0f}" y="{cy:.0f}" width="{size}" height="{size}" fill="{rnd.choice([NEON, MID, "#c8ffb0"])}" '
                         f'style="opacity:0;animation:db{i}_{d} {T}s linear infinite"/>')
        css.append(f"@keyframes pt{i}{{0%,{pc(tk):.3f}%{{opacity:0;transform:translateY(0)}}{pc(tk) + 0.5:.3f}%{{opacity:1;transform:translateY(0)}}"
                   f"{pc(tk) + 9:.3f}%{{opacity:1;transform:translateY(-26px)}}{pc(tk) + 11:.3f}%,100%{{opacity:0;transform:translateY(-30px)}}}}")
        inner.append(f'<g style="opacity:0;animation:pt{i} {T}s linear infinite">{centered(f"+{pts}", cx, cy - bh / 2 - 22, 2 + big, "#c8ffb0")}</g>')
        score += pts
        score_times.append((tk, score))

    # HUD: score that ticks up with each kill, wave label
    hud = [pixel_text("SCORE", 30, 24, 2, DIM)]
    for j, (t0, val) in enumerate(score_times):
        t1 = score_times[j + 1][0] if j + 1 < len(score_times) else T
        css.append(window(f"sc{j}", t0, t1 - 0.001 if j + 1 < len(score_times) else T))
        hud.append(f'<g style="opacity:0;animation:sc{j} {T}s linear infinite">{pixel_text(f"{val:06d}", 100, 24, 2)}</g>')
    hud.append(pixel_text("WAVE 01", w - 30 - text_width("WAVE 01", 2), 24, 2, DIM))
    clip = f'<clipPath id="arn"><rect x="13" y="13" width="{w - 26}" height="{h - 26}" rx="8"/></clipPath>'
    b.append(f'<defs>{clip}</defs><style>{"".join(css)}</style><g clip-path="url(#arn)">{"".join(inner)}</g>')
    b.extend(hud)
    return svg(w, h, "\n".join(b), "Space battle: my fighter shoots down a wave of raiders and a boss ship.")


# --------------------------------------------------------------------------
# GitHub data
# --------------------------------------------------------------------------
def api(path):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "arcade-readme-builder"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch():
    user = api(f"users/{USER}")
    repos = api(f"users/{USER}/repos?per_page=100&type=owner")
    repos = [r for r in repos if r["name"].lower() != USER.lower()]  # not the profile repo itself
    return user, repos


# --------------------------------------------------------------------------
# The pictures
# --------------------------------------------------------------------------
def banner(user, repos):
    w, h = 1000, 330
    stars = sum(r["stargazers_count"] for r in repos)
    own = [r for r in repos if not r["fork"]]
    b = [frame(w, h), starfield(w, h, 70, 7), space(w, h, 101, comets=3, asteroids=3, lanes=(247,), rocks=[(86, 108), (214, 278)], ship=4)]
    b.append(pixel_text("1UP", 40, 34, 3, extra='class="blink"'))
    b.append(pixel_text(f"STARS {stars:06d}", 40, 62, 3))
    b.append(centered("PLAYER 1", w / 2, 34, 3, DIM))
    b.append(centered(f"AGE {PROFILE['age']}", w / 2, 62, 3))
    b.append(pixel_text("REPOS", w - 40 - text_width("REPOS", 3), 34, 3, DIM))
    b.append(pixel_text(f"{len(own):03d}", w - 40 - text_width("000", 3), 62, 3))
    b.append(centered(PROFILE["name"], w / 2, 112, 9, extra='filter="url(#glow)" class="pulse"'))
    b.append(centered(PROFILE["bio"], w / 2, 192, 2.5))
    b.append(centered("INSERT STAR TO CONTINUE", w / 2, 284, 3, extra='class="blink"'))
    return svg(w, h, "\n".join(b), f"{PROFILE['name']}, age {PROFILE['age']}: {PROFILE['bio'].lower()}. Insert star to continue.")


def terminal():
    bio = wrap(PROFILE["bio"], 40)
    lines = [f"> NAME ... {PROFILE['name']}", f"> AGE .... {PROFILE['age']}", f"> BIO .... {bio[0]}"]
    lines += [f"           {rest}" for rest in bio[1:]]
    w, scale, lh = 1000, 3, 38
    text_end = 76 + (len(lines) - 1) * lh + 7 * scale
    h = text_end + 78
    b = [frame(w, h), space(w, h, 202, comets=2, asteroids=2, lanes=(text_end + 32,), rocks=[(text_end + 8, h - 16)], opacity=0.6)]
    b.append(pixel_text("PLAYER SELECT", 34, 30, 3, DIM))
    # Lines pop in one by one. The resting state is visible, so the text still
    # shows if a viewer doesn't run SVG animations.
    b.append("<style>@keyframes boot { 0% { opacity: 0; } 60% { opacity: 1; } 75% { opacity: .3; } 100% { opacity: 1; } }</style>")
    t = 0.3
    for i, line in enumerate(lines):
        y = 76 + i * lh
        b.append(pixel_text(line, 40, y, scale, NEON, f'style="animation: boot .45s steps(4) {t:.2f}s backwards"'))
        t += 0.45
    y = 76 + (len(lines) - 1) * lh
    cx = 40 + text_width(lines[-1], scale) + 10
    b.append(f'<rect x="{cx}" y="{y}" width="{4 * scale}" height="{7 * scale}" fill="{NEON}" class="blink"/>')
    return svg(w, h, "\n".join(b), f"Player select. Name: {PROFILE['name']}. Age: {PROFILE['age']}. Bio: {PROFILE['bio'].lower()}.")


def ordinal(n):
    return f"{n}{'TH' if 10 <= n % 100 <= 20 else {1: 'ST', 2: 'ND', 3: 'RD'}.get(n % 10, 'TH')}"


def highscores(repos):
    own = [r for r in repos if not r["fork"]]
    rank = {n: i for i, n in enumerate(IMPORTANCE)}
    ranked = sorted((r for r in own if r["name"] in rank), key=lambda r: rank[r["name"]])
    rest = sorted((r for r in own if r["name"] not in rank), key=lambda r: r["pushed_at"], reverse=True)
    rest.sort(key=lambda r: r["stargazers_count"], reverse=True)
    own = (ranked + rest)[:10]
    w = 1000
    top, lh = 150, 40
    rows_end = top + (len(own) - 1) * lh + 21
    h = rows_end + 80
    b = [frame(w, h), starfield(w, h, 25, 11), space(w, h, 303, comets=2, asteroids=3, lanes=(rows_end + 34,),
                                                    rocks=[(80, 106), (rows_end + 8, h - 16)], opacity=0.6)]
    b.append(centered("HIGH SCORES", w / 2, 34, 6, extra='filter="url(#glow)"'))
    for x, label in [(60, "RANK"), (220, "PROJECT"), (650, "STARS"), (820, "LANG")]:
        b.append(pixel_text(label, x, 110, 2, DIM))
    for i, r in enumerate(own):
        y = top + i * lh
        name = SHORT_NAME.get(r["name"], r["name"]).upper()[:22]
        fill = NEON if i < 3 else MID
        extra = 'class="blink"' if i == 0 else ""
        b.append(pixel_text(ordinal(i + 1), 60, y, 3, fill, extra))
        b.append(pixel_text(name, 220, y, 3, fill))
        b.append(pixel_text(f"@ {r['stargazers_count']:03d}", 650, y, 3, fill))
        b.append(pixel_text(LANG_SHORT.get(r["language"], (r["language"] or "WEB").upper()[:6]), 820, y, 3, fill))
    return svg(w, h, "\n".join(b), "High scores, ranked by importance: " + ", ".join(
        f"{i + 1}. {SHORT_NAME.get(r['name'], r['name'])}" for i, r in enumerate(own)))


def stats(user, repos):
    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in repos)
    langs = {}
    for r in own:
        key = LANG_SHORT.get(r["language"], (r["language"] or "WEB").upper()[:6])
        langs[key] = langs.get(key, 0) + 1
    langs = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    w = 1000
    ach_end = 100 + max(5, len(langs)) * 36 + 20 + 62 + (len(ACHIEVEMENTS) - 1) * 30 + 14
    h = ach_end + 78
    b = [frame(w, h), space(w, h, 404, comets=2, asteroids=3, lanes=(ach_end + 32,), rocks=[(ach_end + 8, h - 16)], opacity=0.6)]
    b.append(pixel_text("PLAYER STATS", 50, 40, 4, extra='filter="url(#glow)"'))
    b.append(pixel_text("POWER-UPS", 540, 40, 4, extra='filter="url(#glow)"'))
    since = user.get("created_at", "")[:4] or "----"
    rows = [("REPOS", f"{len(own):02d}"), ("STARS", f"{stars:02d}"), ("FOLLOWERS", f"{user.get('followers', 0):02d}"),
            ("AGE", f"{PROFILE['age']}"), ("SINCE", since)]
    for i, (k, v) in enumerate(rows):
        y = 100 + i * 36
        b.append(pixel_text(k, 50, y, 3, DIM))
        b.append(pixel_text("." * (12 - len(k)), 50 + text_width(k + " ", 3), y, 3, DARK))
        b.append(pixel_text(v, 330, y, 3))
    most = max((n for _, n in langs), default=1)
    for i, (lang, n) in enumerate(langs):
        y = 100 + i * 36
        b.append(pixel_text(lang, 540, y, 3, DIM))
        blocks = max(1, round(12 * n / most))
        for j in range(12):
            on = j < blocks
            b.append(f'<rect x="{680 + j * 20}" y="{y}" width="16" height="21" fill="{NEON if on else DARK}"'
                     f'{" class=" + chr(34) + "pulse" + chr(34) if on else ""} style="animation-delay:{j * 0.1:.1f}s"/>')
        b.append(pixel_text(f"{n}", 930, y, 3))
    y0 = 100 + max(5, len(langs)) * 36 + 20
    b.append(f'<line x1="40" y1="{y0}" x2="{w - 40}" y2="{y0}" stroke="{DIM}" stroke-width="2" stroke-dasharray="8 6"/>')
    b.append(pixel_text("ACHIEVEMENTS UNLOCKED", 50, y0 + 22, 3, extra='filter="url(#glow)"'))
    for i, a in enumerate(ACHIEVEMENTS):
        b.append(pixel_text("@ " + a, 70, y0 + 62 + i * 30, 2))
    return svg(w, h, "\n".join(b), f"Player stats: {len(own)} repos, {stars} stars, {user.get('followers', 0)} followers, age {PROFILE['age']}. "
               + "Languages: " + ", ".join(f"{k} {v}" for k, v in langs) + ". Achievements: " + "; ".join(ACHIEVEMENTS))


def header(label, seed):
    w, h = 1000, 70
    b = [space(w, h, seed, comets=1, asteroids=1, rocks=[(6, 64)], opacity=0.7),
         f'<line x1="20" y1="35" x2="{w - 20}" y2="35" stroke="{DIM}" stroke-width="2" stroke-dasharray="6 6"/>']
    tw = text_width(label, 4)
    b.append(f'<rect x="{w / 2 - tw / 2 - 24}" y="10" width="{tw + 48}" height="50" fill="{BG}"/>')
    b.append(centered(label, w / 2, 21, 4, extra='filter="url(#glow)"'))
    return svg(w, h, "\n".join(b), label)


def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + (1 if cur else 0) > width:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}" if cur else wd
    if cur:
        lines.append(cur)
    return lines


def card(r, stage):
    w, h = 490, 180
    name = SHORT_NAME.get(r["name"], r["name"]).upper()[:24]
    desc = TAGLINE.get(r["name"]) or (r.get("description") or "A mystery stage. Enter at your own risk.").strip()
    seed = zlib.crc32(r["name"].encode())  # stable per repo
    b = [frame(w, h, 4, 12), starfield(w, h, 10, seed), space(w, h, seed, comets=1, asteroids=0, opacity=0.5)]
    b.append(pixel_text(name, 26, 26, 3, extra='filter="url(#glow)"'))
    b.append(pixel_text(stage, w - 26 - text_width(stage, 2), 30, 2, DIM))
    for i, line in enumerate(wrap(desc, 46)[:3]):
        b.append(f'<text x="26" y="{82 + i * 21}" fill="{NEON}" font-family="\'Courier New\', Courier, monospace" '
                 f'font-size="15" font-weight="bold">{escape(line)}</text>')
    b.append(pixel_text(f"@ {r['stargazers_count']}", 26, 146, 2))
    b.append(pixel_text(LANG_SHORT.get(r["language"], (r["language"] or "WEB").upper()), 110, 146, 2, DIM))
    b.append(pixel_text("PLAY >", w - 26 - text_width("PLAY >", 2), 146, 2, extra='class="blink"'))
    return svg(w, h, "\n".join(b), f"{name}: {desc} ({r['stargazers_count']} stars)")


def footer():
    w, h = 1000, 200
    b = [frame(w, h), starfield(w, h, 30, 23), space(w, h, 505, comets=3, asteroids=3, lanes=(40, 164), rocks=[(20, 62), (142, 186)], opacity=0.8, ship=3)]
    b.append(centered("GAME OVER", w / 2, 68, 10, extra='filter="url(#glow)" class="pulse"'))
    return svg(w, h, "\n".join(b), "Game over.")


def img(name, alt):
    return f'<p align="center"><img src="assets/{name}" width="100%" alt="{escape(alt, {chr(34): "&quot;"})}"></p>\n\n'


def main():
    try:
        user, repos = fetch()
    except Exception as e:  # keep the last good pictures if GitHub is unreachable
        print(f"GitHub API failed ({e}); keeping existing assets", file=sys.stderr)
        return 0 if os.path.isdir(OUT) else 1
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):  # drop pictures of repos that no longer exist
        if old.endswith(".svg"):
            os.remove(os.path.join(OUT, old))
    files = {
        "banner.svg": banner(user, repos),
        "arena.svg": arena(),
        "profile.svg": terminal(),
        "highscores.svg": highscores(repos),
        "stats.svg": stats(user, repos),
        "footer.svg": footer(),
    }
    by_name = {r["name"]: r for r in repos if not r["fork"]}
    worlds = list(WORLDS)
    extra = [n for n in sorted(by_name, key=lambda n: by_name[n]["pushed_at"], reverse=True)
             if not any(n in names for _, names in WORLDS)]
    if extra:
        worlds.append(("BONUS STAGES", extra))
    sections = []
    for wi, (label, names) in enumerate(worlds, 1):
        slug = f"world{wi}"
        files[f"h-{slug}.svg"] = header(label, 600 + wi)
        links = []
        for si, n in enumerate([n for n in names if n in by_name], 1):
            r = by_name[n]
            files[f"card-{n}.svg"] = card(r, f"STAGE {wi}-{si}")
            alt = f"{SHORT_NAME.get(n, n)}: {TAGLINE.get(n) or r.get('description') or ''}".strip(": ")
            links.append(f'  <a href="{r["html_url"]}"><img src="assets/card-{n}.svg" width="49%" alt="{escape(alt, {chr(34): "&quot;"})}"></a>')
        if links:
            sections.append(img(f"h-{slug}.svg", label) + '<p align="center">\n' + "\n".join(links) + "\n</p>\n")
    for name, body in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
    readme = (
        "<!-- Generated by scripts/build_svgs.py (refreshed daily by .github/workflows/refresh.yml). Edit the script, not this file. -->\n"
        + img("banner.svg", f"{PROFILE['name']}, age {PROFILE['age']}: {PROFILE['bio'].lower()}. Insert star to continue.")
        + img("arena.svg", "Space battle: my fighter shoots down a wave of raiders and a boss ship.")
        + img("profile.svg", f"Player select. Name: {PROFILE['name']}. Age: {PROFILE['age']}. Bio: {PROFILE['bio'].lower()}.")
        + img("highscores.svg", "High scores: my projects ranked by importance.")
        + "\n".join(sections)
        + img("stats.svg", "Player stats, languages and achievements.")
        + img("footer.svg", "Game over.")
    )
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(readme)
    print(f"wrote {len(files)} SVGs to {OUT} and README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
