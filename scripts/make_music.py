"""Synthesizes "Insert Star", an original chiptune for the arcade profile.

Composed and rendered entirely in this file: pulse-wave lead, thin pulse
arpeggios, triangle bass and noise drums, like an 8-bit console. No samples,
no outside music. Dedicated to the public domain (CC0 1.0).

    python scripts/make_music.py      # writes docs/insert-star.wav

Needs numpy.
"""

import os
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "insert-star.wav")

RATE = 22050
BPM = 140
STEP = 60 / BPM / 4          # one 16th note
STEPS_PER_BAR = 16

CHORDS = {
    "Am": ["A", "C", "E"], "F": ["F", "A", "C"], "C": ["C", "E", "G"],
    "G": ["G", "B", "D"], "E": ["E", "G#", "B"],
}
SEMI = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def freq(note):
    """'A4' -> 440 Hz."""
    name, octave = note[:-1], int(note[-1])
    midi = 12 * (octave + 1) + SEMI[name]
    return 440.0 * 2 ** ((midi - 69) / 12)


# --------------------------------------------------------------------------
# The song. Each bar is 16 sixteenth-note slots: a note starts a new note,
# "-" holds the previous one, "." is silence.
# --------------------------------------------------------------------------
A_PART = [
    ("Am", "A4 - C5 - E5 - A5 - G5 - E5 - D5 - E5 -"),
    ("F",  "F5 - - - E5 - C5 - A4 - C5 - F5 - E5 -"),
    ("C",  "E5 - - - G5 - E5 - C5 - - - D5 - E5 -"),
    ("G",  "D5 - - - B4 - G4 - B4 - D5 - G5 - F5 -"),
    ("Am", "E5 - A5 - - - G5 - A5 - B5 - C6 - - -"),
    ("F",  "A5 - - - G5 - F5 - E5 - F5 - A5 - - -"),
    ("C",  "G5 - E5 - C5 - E5 - G5 - - - C6 - B5 -"),
    ("G",  "B5 - - - - - - - G5 - A5 - B5 - D6 -"),
]
B_PART = [
    ("F",  "C6 - - - A5 - - - F5 - A5 - C6 - D6 -"),
    ("G",  "D6 - - - B5 - - - G5 - B5 - D6 - E6 -"),
    ("Am", "E6 - - - - - C6 - A5 - - - E5 - A5 -"),
    ("Am", "C6 - B5 - A5 - G5 - A5 - - - - - . ."),
    ("F",  "F5 - A5 - C6 - A5 - F5 - A5 - C6 - F6 -"),
    ("G",  "D6 - B5 - G5 - B5 - D6 - G6 - F6 - D6 -"),
    ("E",  "E6 - - - D6 - B5 - G#5 - B5 - D6 - E6 -"),
    ("E",  "E6 - - - - - - - . . . . E5 - G#5 -"),
]
INTRO = [(c, ". . . . . . . . . . . . . . . .") for c in ("Am", "F", "C", "G")]
OUTRO = [
    ("Am", "A5 - - - E5 - - - C5 - - - E5 - - -"),
    ("F",  "F5 - - - - - - - A5 - - - - - - -"),
    ("G",  "G5 - - - - - - - B5 - - - D6 - - -"),
    ("Am", "A5 - - - - - - - - - - - . . . ."),
]
SONG = INTRO + A_PART + B_PART + A_PART + OUTRO   # 32 bars, about 55 s, loops cleanly


def envelope(n, attack=0.004, release=0.03, decay_to=0.75, decay=0.12):
    t = np.arange(n) / RATE
    env = np.minimum(1.0, t / attack)
    env *= decay_to + (1 - decay_to) * np.exp(-t / decay)
    rel = int(release * RATE)
    if n > rel:
        env[-rel:] *= np.linspace(1, 0, rel)
    return env


def pulse(f, n, duty, vibrato=0.0):
    t = np.arange(n) / RATE
    if vibrato:
        f = f * (1 + vibrato * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) * 4, 0, 1))
        phase = np.cumsum(f) / RATE
    else:
        phase = f * t
    return np.where(phase % 1.0 < duty, 1.0, -1.0)


def triangle(f, n):
    t = np.arange(n) / RATE
    return 2 * np.abs(2 * ((f * t) % 1.0) - 1) - 1


rng = np.random.default_rng(7)


def noise(n):
    # 8-bit style: hold each random value for a few samples
    hold = 2
    v = rng.choice([-1.0, 1.0], size=n // hold + 1)
    return np.repeat(v, hold)[:n]


def kick(n):
    t = np.arange(n) / RATE
    f = 140 * np.exp(-t * 22) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * 14)


def render():
    total_steps = len(SONG) * STEPS_PER_BAR
    n_total = int(total_steps * STEP * RATE) + RATE
    lead = np.zeros(n_total)
    arp = np.zeros(n_total)
    bass = np.zeros(n_total)
    drums = np.zeros(n_total)

    def at(step):
        return int(round(step * STEP * RATE))

    def add(buf, start, sig):
        end = min(start + len(sig), len(buf))
        buf[start:end] += sig[: end - start]

    for bar, (chord, line) in enumerate(SONG):
        tokens = line.split()
        assert len(tokens) == STEPS_PER_BAR, (bar, line)
        base = bar * STEPS_PER_BAR
        section = "intro" if bar < 4 else "outro" if bar >= len(SONG) - 4 else "B" if 12 <= bar < 20 else "A"
        # lead: find each note and how long it is held
        i = 0
        while i < STEPS_PER_BAR:
            tok = tokens[i]
            if tok in ("-", "."):
                i += 1
                continue
            length = 1
            while i + length < STEPS_PER_BAR and tokens[i + length] == "-":
                length += 1
            n = at(length)
            sig = pulse(freq(tok), n, 0.25, vibrato=0.006 if length >= 4 else 0) * envelope(n)
            add(lead, at(base + i), sig)
            i += length
        # arpeggio: chord tones every 16th, up-down
        notes = CHORDS[chord]
        pattern = [0, 1, 2, 1]
        for s in range(STEPS_PER_BAR):
            name = notes[pattern[s % 4]]
            octave = 5 if section == "B" else 4
            n = at(1)
            sig = pulse(freq(f"{name}{octave}"), n, 0.125) * envelope(n, decay_to=0.35, decay=0.04, release=0.01)
            add(arp, at(base + s), sig)
        # bass: root, octave bounce on 8ths
        root = notes[0]
        for s in range(0, STEPS_PER_BAR, 2):
            octave = 2 if (s // 2) % 2 == 0 else 3
            n = at(2)
            add(bass, at(base + s), triangle(freq(f"{root}{octave}"), n) * envelope(n, decay_to=0.9, release=0.02))
        # drums
        last_bar = bar == len(SONG) - 1
        for s in range(STEPS_PER_BAR):
            if last_bar and s >= 12:
                break
            start = at(base + s)
            if s in (0, 8) or (section == "B" and s in (6, 10)) or (section != "intro" and s == 14 and bar % 4 == 3):
                add(drums, start, kick(int(0.16 * RATE)) * 0.9)
            if s in (4, 12) and section != "intro" or (section == "intro" and s == 12 and bar == 3):
                n = int(0.13 * RATE)
                add(drums, start, noise(n) * np.exp(-np.arange(n) / RATE * 28) * 0.45)
            if s % 2 == 0 or section == "B":
                n = int(0.035 * RATE)
                add(drums, start, noise(n) * np.exp(-np.arange(n) / RATE * 120) * (0.16 if s % 4 == 2 else 0.1))
        # fill into the next section
        if bar % 8 == 3 and section != "outro":
            for s in (12, 13, 14, 15):
                n = int(0.09 * RATE)
                add(drums, at(base + s), noise(n) * np.exp(-np.arange(n) / RATE * 30) * 0.3)

    mix = lead * 0.22 + arp * 0.07 + bass * 0.30 + drums * 0.55
    # gentle low-pass so the square waves aren't harsh
    k = np.ones(3) / 3
    mix = np.convolve(mix, k, mode="same")
    mix = mix[: at(total_steps)]
    peak = np.max(np.abs(mix))
    mix = mix / peak * 0.89
    return mix


def main():
    mix = render()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pcm = (mix * 32767).astype("<i2")
    with wave.open(OUT, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    secs = len(mix) / RATE
    print(f"wrote {OUT}: {secs:.1f} s, {os.path.getsize(OUT) / 1e6:.1f} MB, peak {np.max(np.abs(mix)):.2f}")


if __name__ == "__main__":
    main()
