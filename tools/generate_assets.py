"""
Generate all PNG art assets for Apple Catcher at high resolution.

Everything is drawn procedurally with pygame (no external art needed) using
supersampling for crisp, anti-aliased edges. Run once; the game loads the
resulting PNGs from the ``assets/`` folder.

    python tools/generate_assets.py
"""
import os
import math
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

pygame.init()
pygame.display.set_mode((1, 1))  # needed so image ops have a video context

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
os.makedirs(ASSETS, exist_ok=True)

SS = 3  # supersample factor for icons


# --------------------------------------------------------------------------- #
#  Low-level helpers
# --------------------------------------------------------------------------- #
def surf(w, h):
    return pygame.Surface((int(w), int(h)), pygame.SRCALPHA)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def radial(size, inner, outer, center=(0.5, 0.5), radius=0.5):
    """Radial gradient surface: ``inner`` RGBA at centre -> ``outer`` at edge."""
    s = surf(size, size)
    cx, cy = center[0] * size, center[1] * size
    R = max(1, int(size * radius))
    for rr in range(R, 0, -1):
        t = rr / R
        pygame.draw.circle(s, lerp(inner, outer, t), (int(cx), int(cy)), rr)
    return s


def vertical(size_w, size_h, top, bottom):
    s = surf(size_w, size_h)
    for y in range(int(size_h)):
        t = y / max(1, size_h - 1)
        pygame.draw.line(s, lerp(top, bottom, t), (0, y), (size_w, y))
    return s


def clip_to(art, mask):
    """Keep ``art`` only where ``mask`` is opaque (mask should be white)."""
    out = art.copy()
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def save(s, name, size):
    out = pygame.transform.smoothscale(s, (int(size[0]), int(size[1])))
    pygame.image.save(out, os.path.join(ASSETS, name))
    print("  wrote", name, size)


# --------------------------------------------------------------------------- #
#  Apple
# --------------------------------------------------------------------------- #
def make_apple(out_size=512):
    S = out_size * SS
    cx, cy = S * 0.5, S * 0.55
    r = S * 0.30

    mask = surf(S, S)
    for dx in (-0.13, 0.13):
        pygame.draw.circle(mask, (255, 255, 255, 255),
                           (int(cx + dx * S), int(cy - 0.03 * S)), int(r))
    pygame.draw.circle(mask, (255, 255, 255, 255), (int(cx), int(cy + 0.06 * S)), int(r))
    pygame.draw.ellipse(mask, (255, 255, 255, 255),
                        (cx - r, cy - 0.02 * S, 2 * r, 2 * r * 0.9))

    art = surf(S, S)
    art.blit(mask.copy(), (0, 0))  # white base; recolour below
    base = surf(S, S)
    base.fill((205, 34, 34, 255))
    art.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    # shading
    art.blit(radial(S, (120, 6, 6, 170), (120, 6, 6, 0), (0.6, 0.66), 0.55), (0, 0))
    art.blit(radial(S, (255, 140, 120, 200), (255, 140, 120, 0), (0.37, 0.33), 0.42), (0, 0))
    art.blit(radial(S, (255, 255, 255, 235), (255, 255, 255, 0), (0.34, 0.27), 0.12), (0, 0))

    apple = clip_to(art, mask)

    # stem + leaf (drawn on top, outside the body mask)
    pygame.draw.line(apple, (96, 60, 28),
                     (int(cx), int(cy - r - 0.02 * S)),
                     (int(cx + 0.03 * S), int(cy - r - 0.14 * S)), int(S * 0.022))
    leaf = [(cx + 0.03 * S, cy - r - 0.12 * S),
            (cx + 0.20 * S, cy - r - 0.22 * S),
            (cx + 0.19 * S, cy - r - 0.10 * S),
            (cx + 0.07 * S, cy - r - 0.03 * S)]
    pygame.draw.polygon(apple, (70, 165, 66), [(int(x), int(y)) for x, y in leaf])
    pygame.draw.polygon(apple, (110, 200, 96),
                        [(int(cx + 0.03 * S), int(cy - r - 0.12 * S)),
                         (int(cx + 0.14 * S), int(cy - r - 0.19 * S)),
                         (int(cx + 0.10 * S), int(cy - r - 0.10 * S))])
    save(apple, "apple.png", (out_size, out_size))


# --------------------------------------------------------------------------- #
#  Bomb
# --------------------------------------------------------------------------- #
def make_bomb(out_size=512):
    S = out_size * SS
    cx, cy = S * 0.5, S * 0.57
    r = S * 0.32

    mask = surf(S, S)
    pygame.draw.circle(mask, (255, 255, 255, 255), (int(cx), int(cy)), int(r))

    art = surf(S, S)
    base = surf(S, S); base.fill((34, 34, 40, 255))
    art.blit(mask.copy(), (0, 0)); art.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    art.blit(radial(S, (0, 0, 0, 180), (0, 0, 0, 0), (0.62, 0.68), 0.5), (0, 0))
    art.blit(radial(S, (150, 150, 170, 220), (150, 150, 170, 0), (0.37, 0.35), 0.33), (0, 0))
    art.blit(radial(S, (255, 255, 255, 235), (255, 255, 255, 0), (0.33, 0.30), 0.09), (0, 0))
    bomb = clip_to(art, mask)

    # cap
    pygame.draw.rect(bomb, (120, 120, 130),
                     (cx - 0.07 * S, cy - r - 0.05 * S, 0.14 * S, 0.09 * S),
                     border_radius=int(S * 0.02))
    # fuse
    pts = [(cx, cy - r - 0.02 * S), (cx + 0.09 * S, cy - r - 0.14 * S),
           (cx + 0.02 * S, cy - r - 0.22 * S), (cx + 0.10 * S, cy - r - 0.30 * S)]
    pygame.draw.lines(bomb, (130, 90, 45), False,
                      [(int(x), int(y)) for x, y in pts], int(S * 0.02))
    # spark glow
    sx, sy = int(cx + 0.10 * S), int(cy - r - 0.33 * S)
    glow = radial(int(0.3 * S), (255, 210, 90, 230), (255, 120, 40, 0), radius=0.5)
    bomb.blit(glow, (sx - int(0.15 * S), sy - int(0.15 * S)))
    pygame.draw.circle(bomb, (255, 245, 210), (sx, sy), int(S * 0.02))
    save(bomb, "bomb.png", (out_size, out_size))


# --------------------------------------------------------------------------- #
#  Shield
# --------------------------------------------------------------------------- #
def make_shield(out_size=512):
    S = out_size * SS
    cx = S * 0.5
    top, bot = S * 0.14, S * 0.9
    w = S * 0.34
    pts = [(cx, top), (cx + w, top + S * 0.05), (cx + w, S * 0.5),
           (cx, bot), (cx - w, S * 0.5), (cx - w, top + S * 0.05)]
    ipts = [(int(x), int(y)) for x, y in pts]

    mask = surf(S, S)
    pygame.draw.polygon(mask, (255, 255, 255, 255), ipts)

    art = clip_to(vertical(S, S, (150, 205, 255, 255), (30, 85, 190, 255)), mask)
    art.blit(radial(S, (255, 255, 255, 150), (255, 255, 255, 0), (0.4, 0.3), 0.4), (0, 0))
    art = clip_to(art, mask)
    pygame.draw.polygon(art, (240, 248, 255), ipts, int(S * 0.02))
    # check-mark emblem
    cm = [(cx - 0.12 * S, cy_ := S * 0.48), (cx - 0.02 * S, S * 0.6), (cx + 0.16 * S, S * 0.32)]
    pygame.draw.lines(art, (255, 255, 255), False,
                      [(int(x), int(y)) for x, y in cm], int(S * 0.045))
    save(art, "shield.png", (out_size, out_size))


# --------------------------------------------------------------------------- #
#  Basket-extension token (widen power-up)
# --------------------------------------------------------------------------- #
def make_extend(out_size=512):
    S = out_size * SS
    cx, cy = S * 0.5, S * 0.5

    mask = surf(S, S)
    pygame.draw.circle(mask, (255, 255, 255, 255), (int(cx), int(cy)), int(S * 0.42))
    art = clip_to(radial(S, (90, 220, 210, 255), (18, 130, 150, 255), (0.4, 0.34), 0.6), mask)
    art.blit(radial(S, (255, 255, 255, 120), (255, 255, 255, 0), (0.4, 0.3), 0.4), (0, 0))
    art = clip_to(art, mask)
    pygame.draw.circle(art, (240, 255, 255), (int(cx), int(cy)), int(S * 0.42), int(S * 0.02))
    # double-headed arrow
    y = cy
    pygame.draw.line(art, (255, 255, 255), (cx - 0.24 * S, y), (cx + 0.24 * S, y), int(S * 0.04))
    for sgn in (-1, 1):
        tip = cx + sgn * 0.30 * S
        pygame.draw.polygon(art, (255, 255, 255), [
            (int(tip), int(y)),
            (int(tip - sgn * 0.12 * S), int(y - 0.11 * S)),
            (int(tip - sgn * 0.12 * S), int(y + 0.11 * S))])
    save(art, "extend.png", (out_size, out_size))


# --------------------------------------------------------------------------- #
#  Hearts
# --------------------------------------------------------------------------- #
def _heart_shape(S):
    cx, cy = S * 0.5, S * 0.42
    r = S * 0.2
    pts = []
    for a in range(0, 360, 4):
        t = math.radians(a)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x / 16 * (S * 0.34), cy - y / 16 * (S * 0.34)))
    return [(int(x), int(y)) for x, y in pts]


def make_hearts(out_size=256):
    S = out_size * SS
    pts = _heart_shape(S)

    mask = surf(S, S); pygame.draw.polygon(mask, (255, 255, 255, 255), pts)
    full = clip_to(vertical(S, S, (255, 110, 110, 255), (200, 20, 40, 255)), mask)
    full.blit(radial(S, (255, 255, 255, 170), (255, 255, 255, 0), (0.4, 0.3), 0.3), (0, 0))
    full = clip_to(full, mask)
    save(full, "heart_full.png", (out_size, out_size))

    empty = surf(S, S)
    pygame.draw.polygon(empty, (70, 70, 80, 180), pts)
    pygame.draw.polygon(empty, (120, 120, 130), pts, int(S * 0.03))
    save(empty, "heart_empty.png", (out_size, out_size))


# --------------------------------------------------------------------------- #
#  Basket (player)
# --------------------------------------------------------------------------- #
def make_basket(out_w=512):
    W, H = out_w * 2, int(out_w * 2 * 0.62)
    s = surf(W, H)
    rim_h = int(H * 0.26)
    body = [(W * 0.03, rim_h), (W * 0.97, rim_h), (W * 0.86, H * 0.98), (W * 0.14, H * 0.98)]
    pygame.draw.polygon(s, (170, 110, 55), [(int(x), int(y)) for x, y in body])
    pygame.draw.polygon(s, (120, 72, 34), [(int(x), int(y)) for x, y in body], int(H * 0.02))
    # weave
    for i in range(1, 7):
        yy = rim_h + i * (H - rim_h) // 7
        pygame.draw.line(s, (120, 74, 34), (int(W * 0.08), int(yy)), (int(W * 0.92), int(yy)), int(H * 0.018))
    for i in range(1, 11):
        xx = W * 0.08 + i * (W * 0.84) / 11
        pygame.draw.line(s, (138, 86, 42), (int(xx), int(rim_h + 4)), (int(xx), int(H * 0.95)), int(H * 0.016))
    # rim
    pygame.draw.ellipse(s, (195, 130, 68), (0, 0, W, rim_h * 1.6))
    pygame.draw.ellipse(s, (120, 72, 34), (0, 0, W, rim_h * 1.6), int(H * 0.03))
    pygame.draw.ellipse(s, (120, 80, 44), (int(W * 0.06), int(rim_h * 0.3), int(W * 0.88), int(rim_h * 0.9)))
    save(s, "basket.png", (out_w, int(out_w * 0.62)))


# --------------------------------------------------------------------------- #
#  Forest background (scene)
# --------------------------------------------------------------------------- #
def make_forest(w=1920, h=1680):
    s = pygame.Surface((w, h))
    ground_y = int(h * 0.82)

    # sky
    for y in range(ground_y):
        t = y / ground_y
        s_col = lerp((122, 198, 245), (214, 240, 224), t)
        pygame.draw.line(s, s_col, (0, y), (w, y))
    # sun glow
    sun = (int(w * 0.17), int(h * 0.16))
    for rr in range(int(h * 0.22), 0, -2):
        a = max(0, 60 - int(rr / (h * 0.22) * 60))
        g = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
        pygame.draw.circle(g, (255, 244, 190, a), (rr, rr), rr)
        s.blit(g, (sun[0] - rr, sun[1] - rr))
    pygame.draw.circle(s, (255, 248, 210), sun, int(h * 0.05))

    # clouds
    rnd = random.Random(3)
    for _ in range(7):
        cx = rnd.randint(0, w); cy = rnd.randint(int(h * 0.05), int(h * 0.4))
        for dx, dy, rr in [(-70, 15, 45), (0, 0, 66), (70, 18, 50), (140, 26, 40)]:
            cl = pygame.Surface((rr * 3, rr * 3), pygame.SRCALPHA)
            pygame.draw.circle(cl, (255, 255, 255, 180), (int(rr * 1.5), int(rr * 1.5)), rr)
            s.blit(cl, (cx + dx - rr, cy + dy - rr))

    def tree(x, top_y, scale, greens):
        tw = int(40 * scale)
        pygame.draw.rect(s, (96, 64, 34), (x - tw // 2, top_y, tw, ground_y - top_y + 40))
        r = int(120 * scale)
        cx, cy = x, top_y - int(20 * scale)
        for col, ox, oy, rf in [(greens[0], 0, 0, 1.0), (greens[0], -0.6, 0.3, 0.78),
                                (greens[0], 0.6, 0.3, 0.78), (greens[1], -0.3, -0.2, 0.62),
                                (greens[1], 0.35, -0.1, 0.58), (greens[2], -0.05, -0.45, 0.42)]:
            pygame.draw.circle(s, col, (int(cx + ox * r), int(cy + oy * r)), int(r * rf))

    # far hazy tree line
    rnd = random.Random(11)
    x = -40
    while x < w + 80:
        tree(x, rnd.randint(int(h * 0.30), int(h * 0.42)), rnd.uniform(0.6, 0.9),
             [(60, 120, 80), (74, 140, 92), (96, 160, 110)])
        x += rnd.randint(150, 240)
    # near rich trees
    rnd = random.Random(7)
    x = 20
    while x < w + 100:
        tree(x, rnd.randint(int(h * 0.12), int(h * 0.26)), rnd.uniform(0.95, 1.5),
             [(32, 108, 44), (52, 140, 58), (96, 178, 72)])
        x += rnd.randint(190, 300)

    # ground
    pygame.draw.rect(s, (66, 128, 42), (0, ground_y, w, h - ground_y))
    pygame.draw.rect(s, (104, 176, 66), (0, ground_y, w, int(h * 0.05)))
    rnd = random.Random(5)
    for _ in range(600):
        gx = rnd.randint(0, w); gy = rnd.randint(ground_y, h)
        bl = rnd.randint(4, 12)
        pygame.draw.line(s, (84, 150, 54), (gx, gy), (gx, gy - bl), 2)

    pygame.image.save(s, os.path.join(ASSETS, "forest_bg.png"))
    print("  wrote forest_bg.png", (w, h))


# --------------------------------------------------------------------------- #
#  Logo + window icon
# --------------------------------------------------------------------------- #
def make_logo():
    apple = pygame.image.load(os.path.join(ASSETS, "apple.png"))
    W, H = 1300, 520
    s = surf(W, H)

    big = pygame.transform.smoothscale(apple, (360, 360))
    s.blit(big, (40, 70))

    font = pygame.font.SysFont("arialrounded,arial", 150, bold=True)
    sub = pygame.font.SysFont("arialrounded,arial", 56, bold=True)

    def stamp(txt, f, x, y, col, outline=(20, 50, 20)):
        base = f.render(txt, True, col)
        for ox in (-4, 4):
            for oy in (-4, 4):
                o = f.render(txt, True, outline)
                s.blit(o, (x + ox, y + oy))
        s.blit(base, (x, y))

    stamp("APPLE", font, 440, 90, (255, 90, 80))
    stamp("CATCHER", font, 440, 240, (255, 214, 92))
    stamp("~ forest edition ~", sub, 446, 420, (235, 255, 235), (30, 70, 40))

    pygame.image.save(s, os.path.join(ASSETS, "logo.png"))
    print("  wrote logo.png", (W, H))

    icon = pygame.transform.smoothscale(apple, (256, 256))
    pygame.image.save(icon, os.path.join(ASSETS, "icon.png"))
    print("  wrote icon.png", (256, 256))


if __name__ == "__main__":
    print("Generating assets into", ASSETS)
    make_apple()
    make_bomb()
    make_shield()
    make_extend()
    make_hearts()
    make_basket()
    make_forest()
    make_logo()
    print("Done.")
