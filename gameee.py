"""Backward-compatible launcher.

The game lives in the ``apple_catcher`` package. This thin shim keeps the
old `python gameee.py` command working; prefer `python main.py`.
"""
from apple_catcher import Game

if __name__ == "__main__":
    Game().run()
