# 🍎 Apple Catcher

A fast little arcade catching game built with **pygame**. Apples tumble down
from a forest canopy — slide your basket along the grass to catch them. But
watch out: some apples **curve** to fool you, some **turn into bombs mid-fall**,
and catching a bomb ends the game with a bang.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![pygame](https://img.shields.io/badge/pygame-2.6-green)

## Gameplay

- 🍎 **Catch apples** to score. Each apple is worth one point.
- ⚡ **It gets harder.** The fall speed ramps up the longer you survive and the
  more apples you bank — up to a capped maximum so it stays playable.
- 🌀 **Deceptive paths.** Many apples drift along a curved, sine-wave path
  instead of falling straight, so you can't just park the basket underneath.
- 💣 **Transforming bombs.** Some apples morph into a lit bomb partway down.
  Read the fall before you commit to a catch.
- 💥 **One bomb and you're out.** Catching a bomb triggers an explosion (with
  sound) and the game is over.
- 🏆 **High score** is saved between sessions in `highscore.txt`.

## Screens

- **Main menu** — start a new game, see your all-time high score, or quit.
- **In-game HUD** — live apple count, current best, and apples missed.
- **Game over** — a polished end panel showing your score, your best, a
  "New High Score!" badge when you beat it, and quick replay / menu buttons.

## Controls

| Action              | Keys                              |
| ------------------- | --------------------------------- |
| Move basket         | `←` / `→`  or  `A` / `D`          |
| Start game (menu)   | `New Game` button or `Enter`      |
| Play again (over)   | `Play Again` button or `R`        |
| Back to menu        | `Main Menu` button or `M`         |
| Minimize window     | `_` button (top-right)            |
| Maximize / windowed | `▣` button (top-right) or `F11`   |
| Back / quit         | `Esc`                             |

The window is **resizable** — drag any edge and the forest, basket, and
falling objects re-lay themselves to fit.

## Requirements

- Python 3.8+
- [pygame](https://www.pygame.org/) 2.x

A virtual environment with pygame is already included in `.venv/`.

## Run

Using the bundled virtual environment:

```bash
.venv/bin/python gameee.py
```

Or with your own environment:

```bash
pip install pygame
python gameee.py
```

> **Audio note:** the explosion sound is generated at runtime (no audio file
> needed). If your system has no audio device, the game detects this and runs
> silently without crashing.

## Project layout

```
Star-Catcher/
├── gameee.py       # the whole game (single file, no external assets)
├── highscore.txt   # created on first play; stores your best score
├── README.md
└── .venv/          # bundled pygame environment
```

## How it works (a peek under the hood)

Everything is drawn with pygame primitives — there are **no image or sound
assets on disk**:

- The forest background (sky gradient, sun, clouds, grass, layered trees) is
  rendered **once per window size** onto a cached surface for smooth frame
  rates.
- Apples and bombs are composed from circles, lines, and polygons.
- Motion is **delta-time based**, so speed is consistent regardless of frame
  rate.
- The explosion sound is synthesized into an in-memory WAV (a noise burst plus
  a low rumble with an exponential decay envelope) using Python's built-in
  `wave` module.

Enjoy, and don't catch the bomb! 💣
