"""Transient visual effects: the bomb explosion."""
import math
import random

import pygame


class Blast:
    """An expanding flash plus flying debris. Lives for ~0.85s."""

    DURATION = 0.85

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.t = 0.0
        self.parts = []
        for _ in range(28):
            self.parts.append({
                "ang": random.uniform(0, math.tau),
                "spd": random.uniform(150, 440),
                "r": random.randint(4, 11),
                "col": random.choice([(255, 170, 40), (255, 90, 40), (90, 90, 90),
                                      (255, 220, 120), (60, 60, 60)]),
            })

    @property
    def done(self):
        return self.t >= self.DURATION

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        t = self.t
        cx, cy = self.x, self.y
        flash_r = int(30 + 280 * min(1.0, t / 0.5))
        alpha = max(0, 220 - int(300 * t))
        if alpha > 0:
            s = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 180, 60, alpha), (flash_r, flash_r), flash_r)
            pygame.draw.circle(s, (255, 240, 180, min(255, alpha + 40)),
                               (flash_r, flash_r), flash_r // 2)
            screen.blit(s, (cx - flash_r, cy - flash_r))
        for p in self.parts:
            px = cx + math.cos(p["ang"]) * p["spd"] * t
            py = cy + math.sin(p["ang"]) * p["spd"] * t + 130 * t * t
            rr = max(1, int(p["r"] * (1.0 - t)))
            pygame.draw.circle(screen, p["col"], (int(px), int(py)), rr)
