"""Procedurally synthesized sound effects (no audio files required).

Each effect is rendered into an in-memory WAV buffer with the standard library
``wave`` module, so there is no dependency on numpy or any sound asset.
"""
import io
import math
import struct
import random

import pygame

SAMPLE_RATE = 44100


def _sound_from_samples(samples):
    """Pack mono float samples [-1, 1] into a stereo 16-bit pygame Sound."""
    buf = io.BytesIO()
    w = wave_open(buf)
    frames = bytearray()
    for s in samples:
        s = max(-1.0, min(1.0, s))
        v = int(s * 32767 * 0.9)
        frames += struct.pack("<hh", v, v)
    w.writeframes(bytes(frames))
    w.close()
    buf.seek(0)
    return pygame.mixer.Sound(file=buf)


def wave_open(buf):
    import wave
    w = wave.open(buf, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SAMPLE_RATE)
    return w


def _explosion():
    dur = 0.9
    n = int(SAMPLE_RATE * dur)
    rnd = random.Random(99)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        noise = (rnd.random() * 2 - 1) * 0.55 * math.exp(-t * 6.0)
        rumble = (math.sin(2 * math.pi * 52 * t) * 0.6 +
                  math.sin(2 * math.pi * 38 * t) * 0.4) * 0.7 * math.exp(-t * 7.5)
        out.append((noise + rumble) * 1.25)
    return out


def _pop():
    """Short pluck for catching an apple."""
    dur = 0.12
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        f = 520 + 300 * math.exp(-t * 30)
        out.append(math.sin(2 * math.pi * f * t) * math.exp(-t * 22) * 0.6)
    return out


def _chime():
    """Bright two-tone chime for picking up a power-up."""
    dur = 0.35
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 7)
        s = (math.sin(2 * math.pi * 660 * t) + math.sin(2 * math.pi * 990 * t)) * 0.35 * env
        out.append(s)
    return out


class Audio:
    """Loads (synthesizes) and plays the game's sound effects."""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            return
        try:
            self.sounds = {
                "boom": _sound_from_samples(_explosion()),
                "pop": _sound_from_samples(_pop()),
                "chime": _sound_from_samples(_chime()),
            }
        except Exception:
            self.enabled = False

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()
