"""Reusable UI primitives: buttons, hearts, the power-up timer bar, HUD."""
import pygame

from . import settings as S


class Button:
    def __init__(self, text, font, base, hover, text_col=S.WHITE):
        self.text = text
        self.font = font
        self.base = base
        self.hover = hover
        self.text_col = text_col
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.enabled = True

    def place(self, center, size):
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        return self

    def draw(self, screen, mouse):
        hovered = self.enabled and self.rect.collidepoint(mouse)
        col = self.hover if hovered else self.base
        if not self.enabled:
            col = (90, 90, 95)
        shadow = self.rect.move(0, 4)
        pygame.draw.rect(screen, (0, 0, 0), shadow, border_radius=16)
        pygame.draw.rect(screen, col, self.rect, border_radius=16)
        pygame.draw.rect(screen, S.WHITE, self.rect, width=2, border_radius=16)
        label = self.font.render(self.text, True, self.text_col if self.enabled else (200, 200, 200))
        screen.blit(label, label.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


def text_center(screen, text, font, cx, cy, color, shadow=True):
    if shadow:
        sh = font.render(text, True, S.BLACK)
        screen.blit(sh, sh.get_rect(center=(cx + 2, cy + 2)))
    img = font.render(text, True, color)
    screen.blit(img, img.get_rect(center=(cx, cy)))


def draw_hearts(screen, assets, lives, max_lives, topleft):
    x, y = topleft
    size = 40
    gap = 8
    for i in range(max_lives):
        name = "heart_full" if i < lives else "heart_empty"
        img = assets.scaled(name, (size, size))
        screen.blit(img, (x + i * (size + gap), y))


def draw_powerup_bar(screen, assets, timers, width):
    """Top-centre chips showing each active power-up and its remaining time."""
    chips = []
    if timers["shield"] > 0:
        chips.append(("shield", timers["shield"], S.SHIELD_CLR))
    if timers["extend"] > 0:
        chips.append(("extend", timers["extend"], S.EXTEND_CLR))
    if timers["boost"] > 0:
        chips.append(("apple", timers["boost"], S.BOOST_CLR))  # boost uses apple glyph

    if not chips:
        return
    chip_w, chip_h = 118, 48
    gap = 12
    total = len(chips) * chip_w + (len(chips) - 1) * gap
    x = width // 2 - total // 2
    y = 16
    for kind, remaining, color in chips:
        rect = pygame.Rect(x, y, chip_w, chip_h)
        s = pygame.Surface((chip_w, chip_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, rect.topleft)
        pygame.draw.rect(screen, color, rect, width=2, border_radius=12)
        icon = assets.scaled(kind, (34, 34))
        screen.blit(icon, (x + 8, y + 7))
        label = assets.font_small.render(f"{remaining:0.0f}s", True, S.WHITE)
        screen.blit(label, label.get_rect(midleft=(x + 50, y + chip_h // 2)))
        x += chip_w + gap


def window_button_rects(width):
    size = 38
    y = 12
    max_btn = pygame.Rect(width - 2 * size - 20, y, size, size)
    min_btn = pygame.Rect(width - size - 12, y, size, size)
    return min_btn, max_btn


def draw_window_buttons(screen, width, is_fullscreen, mouse):
    min_btn, max_btn = window_button_rects(width)
    for rect, kind in ((min_btn, "min"), (max_btn, "max")):
        hovered = rect.collidepoint(mouse)
        pygame.draw.rect(screen, (248, 248, 248) if hovered else (228, 228, 228),
                         rect, border_radius=8)
        pygame.draw.rect(screen, (90, 90, 90), rect, width=2, border_radius=8)
        cx, cy = rect.center
        if kind == "min":
            pygame.draw.line(screen, (40, 40, 40), (cx - 9, cy + 7), (cx + 9, cy + 7), 3)
        elif is_fullscreen:
            pygame.draw.rect(screen, (40, 40, 40), (cx - 5, cy - 8, 12, 12), 2)
            pygame.draw.rect(screen, (40, 40, 40), (cx - 9, cy - 4, 12, 12), 2)
        else:
            pygame.draw.rect(screen, (40, 40, 40), (cx - 9, cy - 9, 18, 18), 2)
    return min_btn, max_btn
