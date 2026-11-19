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
    cx = S * 0.5

    # Silhouette: one large body circle gives a single clean round bottom; two
    # higher "shoulder" circles widen the top and leave a dimple at top-centre
    # for the stem. The shoulders sit inside the body lower down, so they never
    # create a second bump at the bottom.
    mask = surf(S, S)
    # A single clean ellipse body, a touch taller than wide.
    pygame.draw.ellipse(mask, (255, 255, 255, 255), (cx - 0.275 * S, 0.29 * S, 0.55 * S, 0.57 * S))

    art = surf(S, S)
    art.blit(mask.copy(), (0, 0))  # white base; recolour below
    base = surf(S, S)
    base.fill((206, 36, 36, 255))
    art.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    # shading: dark vignette lower-right, warm glow upper-left, glossy specular
    art.blit(radial(S, (120, 8, 8, 175), (120, 8, 8, 0), (0.60, 0.66), 0.54), (0, 0))
    art.blit(radial(S, (255, 150, 130, 205), (255, 150, 130, 0), (0.38, 0.40), 0.44), (0, 0))
    art.blit(radial(S, (255, 255, 255, 240), (255, 255, 255, 0), (0.37, 0.34), 0.10), (0, 0))
    apple = clip_to(art, mask)

    # small dark dimple at the very top where the stem sits
    pygame.draw.circle(apple, (120, 16, 16, 110), (int(cx), int(S * 0.30)), int(S * 0.035))

    # stem + two-tone leaf (drawn above the body)
    topy = S * 0.30
    pygame.draw.line(apple, (96, 60, 28),
                     (int(cx), int(topy)), (int(cx + 0.02 * S), int(topy - 0.11 * S)), int(S * 0.022))
    leaf = [(cx + 0.02 * S, topy - 0.09 * S),
            (cx + 0.20 * S, topy - 0.15 * S),
            (cx + 0.19 * S, topy - 0.02 * S),
            (cx + 0.05 * S, topy - 0.01 * S)]
    pygame.draw.polygon(apple, (64, 158, 60), [(int(x), int(y)) for x, y in leaf])
    pygame.draw.polygon(apple, (108, 198, 94),
                        [(int(cx + 0.03 * S), int(topy - 0.07 * S)),
                         (int(cx + 0.14 * S), int(topy - 0.12 * S)),
                         (int(cx + 0.11 * S), int(topy - 0.03 * S))])
    # leaf vein
    pygame.draw.line(apple, (40, 120, 44),
                     (int(cx + 0.05 * S), int(topy - 0.05 * S)),
                     (int(cx + 0.19 * S), int(topy - 0.11 * S)), int(S * 0.008))
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

    def tree(x, top_y, scale, greens, speckle=True, rnd=None):
        """A fuller tree: tapered shaded trunk + a rounded, dimensional canopy.

        ``greens`` = (underside, dark, mid, light) shades, dark -> light.
        """
        under, dark, mid, light = greens
        base_y = ground_y + 40
        tw = 46 * scale
        # tapered trunk (wider at the base)
        canopy_y = top_y - int(14 * scale)
        trunk = [(x - tw * 0.55, base_y), (x + tw * 0.55, base_y),
                 (x + tw * 0.26, canopy_y + 30 * scale), (x - tw * 0.26, canopy_y + 30 * scale)]
        pygame.draw.polygon(s, (104, 70, 38), [(int(a), int(b)) for a, b in trunk])
        pygame.draw.line(s, (128, 90, 52), (x - tw * 0.34, base_y),
                         (x - tw * 0.16, canopy_y), max(2, int(5 * scale)))   # lit side
        pygame.draw.line(s, (74, 48, 26), (x + tw * 0.38, base_y),
                         (x + tw * 0.18, canopy_y), max(3, int(8 * scale)))   # shadow side
        # a couple of branches
        for sgn in (-1, 1):
            pygame.draw.line(s, (92, 60, 32),
                             (int(x), int(canopy_y + 50 * scale)),
                             (int(x + sgn * 55 * scale), int(canopy_y + 8 * scale)),
                             max(2, int(7 * scale)))

        r = 120 * scale
        cx, cy = x, canopy_y - int(8 * scale)
        blob = [(0, 0.05, 1.0), (-0.58, 0.28, 0.72), (0.58, 0.28, 0.72),
                (-0.33, -0.28, 0.64), (0.33, -0.28, 0.64), (0, -0.52, 0.5),
                (0, 0.42, 0.74)]
        # underside / dark base
        for ox, oy, rf in blob:
            pygame.draw.circle(s, dark, (int(cx + ox * r), int(cy + oy * r)), int(r * rf))
        for ox, oy, rf in [(0, 0.5, 0.6), (-0.42, 0.42, 0.44), (0.42, 0.42, 0.44)]:
            pygame.draw.circle(s, under, (int(cx + ox * r), int(cy + oy * r)), int(r * rf))
        # mid tone, nudged up
        for ox, oy, rf in blob:
            pygame.draw.circle(s, mid, (int(cx + ox * r), int(cy + (oy - 0.12) * r)), int(r * rf * 0.82))
        # top-left highlights
        for ox, oy, rf in [(-0.3, -0.4, 0.42), (-0.03, -0.55, 0.32), (0.22, -0.34, 0.3),
                           (-0.45, -0.12, 0.3)]:
            pygame.draw.circle(s, light, (int(cx + ox * r), int(cy + oy * r)), int(r * rf))
        # leaf speckles for texture
        if speckle and rnd is not None:
            for _ in range(int(26 * scale)):
                a = rnd.uniform(0, 6.283); rad = rnd.uniform(0, r * 0.95)
                px, py = cx + math.cos(a) * rad, cy + math.sin(a) * rad * 0.85
                pygame.draw.circle(s, light if rnd.random() < 0.5 else mid,
                                   (int(px), int(py)), max(1, int(3 * scale)))

    # far hazy tree line (bluish, low contrast)
    rnd = random.Random(11)
    x = -40
    while x < w + 80:
        tree(x, rnd.randint(int(h * 0.30), int(h * 0.42)), rnd.uniform(0.6, 0.9),
             [(70, 118, 96), (86, 134, 104), (104, 152, 118), (128, 176, 138)],
             speckle=False)
        x += rnd.randint(150, 240)
    # near rich trees
    rnd = random.Random(7)
    x = 20
    while x < w + 100:
        tree(x, rnd.randint(int(h * 0.12), int(h * 0.26)), rnd.uniform(1.0, 1.5),
             [(22, 86, 38), (34, 112, 46), (58, 146, 62), (104, 190, 86)], rnd=rnd)
        x += rnd.randint(200, 300)

    # ground
    pygame.draw.rect(s, (66, 128, 42), (0, ground_y, w, h - ground_y))
    pygame.draw.rect(s, (104, 176, 66), (0, ground_y, w, int(h * 0.05)))
    # bushes along the forest floor for depth
    rnd = random.Random(21)
    x = 40
    while x < w:
        bx, by, bs = x, ground_y + int(rnd.uniform(0, 30)), rnd.uniform(0.5, 1.0)
        for ox, oy, rf in [(0, 0, 1.0), (-0.6, 0.15, 0.7), (0.6, 0.15, 0.7), (0, -0.3, 0.6)]:
            pygame.draw.circle(s, (46, 110, 40),
                               (int(bx + ox * 70 * bs), int(by + oy * 70 * bs)), int(70 * bs * rf))
        for ox, oy, rf in [(-0.2, -0.3, 0.45), (0.25, -0.2, 0.4)]:
            pygame.draw.circle(s, (74, 150, 60),
                               (int(bx + ox * 70 * bs), int(by + oy * 70 * bs)), int(70 * bs * rf))
        x += rnd.randint(150, 320)
    # grass blades
    rnd = random.Random(5)
    for _ in range(800):
        gx = rnd.randint(0, w); gy = rnd.randint(ground_y, h)
        bl = rnd.randint(5, 14)
        pygame.draw.line(s, (84, 150, 54), (gx, gy), (gx + rnd.randint(-2, 2), gy - bl), 2)

    pygame.image.save(s, os.path.join(ASSETS, "forest_bg.png"))
    print("  wrote forest_bg.png", (w, h))


# --------------------------------------------------------------------------- #
#  Logo + window icon
# --------------------------------------------------------------------------- #
def make_icon():
    """Window/taskbar icon, derived from the apple."""
    apple = pygame.image.load(os.path.join(ASSETS, "apple.png"))
    icon = pygame.transform.smoothscale(apple, (256, 256))
    pygame.image.save(icon, os.path.join(ASSETS, "icon.png"))
    print("  wrote icon.png", (256, 256))


def make_logo(force=False):
    """Default procedural logo. Skipped if a logo already exists so a
    user-supplied ``logo.png`` is never clobbered (pass force=True to override).
    """
    logo_path = os.path.join(ASSETS, "logo.png")
    if os.path.exists(logo_path) and not force:
        print("  kept existing logo.png (use --force-logo to regenerate)")
        return
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

    pygame.image.save(s, logo_path)
    print("  wrote logo.png", (W, H))


if __name__ == "__main__":
    import sys
    force_logo = "--force-logo" in sys.argv
    print("Generating assets into", ASSETS)
    make_apple()
    make_bomb()
    make_shield()
    make_extend()
    make_hearts()
    make_basket()
    make_forest()
    make_icon()
    make_logo(force=force_logo)
    print("Done.")
