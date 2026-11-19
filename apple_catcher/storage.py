"""Tiny persistence layer for the high score."""
from . import settings


def load_highscore():
    try:
        with open(settings.HIGHSCORE_FILE) as f:
            return int(f.read().strip() or "0")
    except (OSError, ValueError):
        return 0


def save_highscore(value):
    try:
        with open(settings.HIGHSCORE_FILE, "w") as f:
            f.write(str(int(value)))
    except OSError:
        pass
