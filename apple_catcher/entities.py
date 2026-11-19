"""Game actors: the falling objects and the player's basket."""
import math
import random

import pygame

from . import settings as S

APPLE, BOMB, SHIELD, EXTEND = "apple", "bomb", "shield", "extend"


class FallingObject:
    """An apple, bomb, or power-up falling from the top of the screen.

    Apples and bombs may follow a curved path and can morph into each other
    partway down; power-ups fall straight-ish and never transform.
    """

    def __init__(self, width, height):
        roll = random.random()
        if roll < S.P_SHIELD:
            self.kind = SHIELD
        elif roll < S.P_SHIELD + S.P_EXTEND:
            self.kind = EXTEND
        elif roll < S.P_SHIELD + S.P_EXTEND + S.P_BOMB:
            self.kind = BOMB
        else:
            self.kind = APPLE

        self.size = S.OBJ_SIZE
        self.radius = self.size * 0.5
        curved = random.random() < S.CURVE_CHANCE
        self.amp = random.randint(*S.CURVE_AMP) if curved else 0
        margin = self.radius + 6 + self.amp
        self.base_x = random.uniform(min(margin, width / 2),
                                     max(width - margin, width / 2))
        self.base_x = max(self.radius + 4, min(width - self.radius - 4, self.base_x))
        self.x = self.base_x
        self.y = -self.radius
        self.freq = random.uniform(0.012, 0.024)
        self.phase = random.uniform(0, math.tau)
        self.spin = 0.0

        # Mid-fall apple<->bomb transformation
        self.morph_to = None
        self.morph_y = None
        if self.kind in (APPLE, BOMB) and random.random() < S.TRANSFORM_CHANCE:
            self.morph_to = BOMB if self.kind == APPLE else APPLE
            self.morph_y = random.uniform(height * 0.35, height * 0.68)
        self.just_morphed = 0.0  # brief pulse timer after morphing

    def update(self, dt, speed, width, height):
        self.y += speed * dt
        if self.amp:
            self.x = self.base_x + self.amp * math.sin(self.freq * self.y + self.phase)
            self.x = max(self.radius, min(width - self.radius, self.x))
        else:
            self.x = self.base_x
        if self.kind == BOMB:
            self.spin += dt * 2.0
        if self.morph_to and self.y >= self.morph_y:
            self.kind = self.morph_to
            self.morph_to = None
            self.just_morphed = 0.25
        if self.just_morphed > 0:
            self.just_morphed -= dt

    @property
    def is_bomb(self):
        return self.kind == BOMB

    @property
    def is_apple(self):
        return self.kind == APPLE

    def rect(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def off_screen(self, height):
        return self.y - self.radius > height

    def draw(self, screen, assets):
        size = self.size
        if self.just_morphed > 0:  # little pop when it transforms
            size = int(size * (1.0 + self.just_morphed))
        img = assets.scaled(self.kind, (size, size))
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(img, rect)


class Basket:
    """The player's basket. Slides horizontally; can grow and speed-boost."""

    def __init__(self, width):
        self.base_w = S.BASKET_BASE_W
        self.ext_w = S.BASKET_EXTEND_W
        self.h = S.BASKET_H
        self.w = self.base_w
        self.extended = False
        self.x = width / 2 - self.w / 2

    def set_extended(self, extended, width):
        cx = self.x + self.w / 2
        self.extended = extended
        self.w = self.ext_w if extended else self.base_w
        self.x = cx - self.w / 2
        self.clamp(width)

    def clamp(self, width):
        self.x = max(0, min(width - self.w, self.x))

    def center_in(self, width):
        self.x = width / 2 - self.w / 2

    def update(self, dt, keys, width, speed_mult=1.0):
        speed = S.BASKET_SPEED * speed_mult
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += speed * dt
        self.clamp(width)

    def catch_rect(self):
        """A forgiving catch zone just inside the basket rim."""
        inset = self.w * 0.09
        return pygame.Rect(self.x + inset, self.y + 6, self.w - inset * 2, 46)

    @property
    def y(self):
        return self._y

    def set_y(self, y):
        self._y = y

    def draw(self, screen, assets, y, shield_on=False):
        self._y = y
        img = assets.scaled("basket", (int(self.w), int(self.h)))
        screen.blit(img, (int(self.x), int(y)))
        if shield_on:
            cx = int(self.x + self.w / 2)
            cy = int(y + self.h / 2)
            rad = int(self.w * 0.62)
            bubble = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(bubble, (120, 190, 255, 60), (rad, rad), rad)
            pygame.draw.circle(bubble, (150, 210, 255, 180), (rad, rad), rad, 4)
            screen.blit(bubble, (cx - rad, cy - rad))
