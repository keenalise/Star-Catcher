"""Image and font loading with a scaled-surface cache."""
import os

import pygame

from . import settings

IMAGE_NAMES = [
    "apple", "bomb", "shield", "extend",
    "heart_full", "heart_empty", "basket",
    "forest_bg", "logo", "icon",
]


class Assets:
    def __init__(self):
        self.orig = {}
        for name in IMAGE_NAMES:
            path = os.path.join(settings.ASSETS_DIR, name + ".png")
            self.orig[name] = pygame.image.load(path).convert_alpha()

        self._scaled = {}
        self._bg_cache = (None, None)  # (size, surface)

        def font(size, bold=True):
            return pygame.font.SysFont("arialrounded,verdana,arial", size, bold=bold)

        self.font_title = font(76)
        self.font_big = font(60)
        self.font_mid = font(38)
        self.font_small = font(27)
        self.font_tiny = font(21)

    def img(self, name):
        return self.orig[name]

    def scaled(self, name, size):
        w, h = int(size[0]), int(size[1])
        key = (name, w, h)
        if key not in self._scaled:
            self._scaled[key] = pygame.transform.smoothscale(self.orig[name], (w, h))
        return self._scaled[key]

    def background(self, size):
        """Forest background scaled to the current window (cached)."""
        size = (int(size[0]), int(size[1]))
        if self._bg_cache[0] != size:
            scaled = pygame.transform.smoothscale(self.orig["forest_bg"], size)
            self._bg_cache = (size, scaled)
        return self._bg_cache[1]

    def window_icon(self):
        return self.orig["icon"]
