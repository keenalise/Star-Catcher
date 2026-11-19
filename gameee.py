import pygame
import random
import math
import os
import io
import wave
import struct

# ============================================================================
#  APPLE CATCHER  -  a forest catching game
#
#  * Apples fall from the trees; move the basket to catch them.
#  * The fall speed ramps up the longer you survive and the more you catch.
#  * Some apples curve sideways mid-air to throw you off.
#  * Some apples turn into bombs partway down -- don't get fooled!
#  * Catch a bomb and it blows up (with sound). Game over.
#
#  Controls:  <- / ->  (or A / D) move   |   Esc back/quit
#  Top-right window buttons:  _  minimize   []  maximize (fullscreen)
# ============================================================================

pygame.init()
try:
    pygame.mixer.init()
    HAS_AUDIO = True
except Exception:
    HAS_AUDIO = False

HERE = os.path.dirname(os.path.abspath(__file__))
HIGHSCORE_FILE = os.path.join(HERE, "highscore.txt")

# ---- Window / display ------------------------------------------------------
WINDOWED_W, WINDOWED_H = 900, 800
WIDTH, HEIGHT = WINDOWED_W, WINDOWED_H
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Apple Catcher")
clock = pygame.time.Clock()
FPS = 60
is_fullscreen = False

# ---- Colors ----------------------------------------------------------------
WHITE       = (255, 255, 255)
BLACK       = (20, 20, 24)
SKY_TOP     = (135, 206, 250)
SKY_BOTTOM  = (221, 243, 223)
GRASS_LIGHT = (104, 176, 66)
GRASS_DARK  = (70, 132, 44)
TRUNK       = (101, 67, 33)
LEAF_DARK   = (34, 110, 44)
LEAF_MID    = (52, 140, 58)
LEAF_LIGHT  = (96, 178, 72)
APPLE_RED   = (210, 40, 40)
APPLE_DARK  = (150, 24, 24)
APPLE_SHINE = (255, 175, 165)
STEM_BROWN  = (92, 60, 30)
LEAF_GREEN  = (80, 170, 70)
BOMB_BLACK  = (28, 28, 32)
BOMB_GRAY   = (95, 95, 108)
FUSE_BROWN  = (120, 80, 40)
SPARK       = (255, 200, 60)
PANEL_BG    = (26, 32, 30)
ACCENT      = (235, 70, 60)
GOLD        = (255, 205, 70)

# ---- Fonts -----------------------------------------------------------------
def _font(size, bold=True):
    return pygame.font.SysFont("arialrounded,verdana,arial", size, bold=bold)

font_title = _font(84)
font_big   = _font(64)
font_mid   = _font(40)
font_small = _font(28)
font_tiny  = _font(22)

# ---- Falling-object settings ----------------------------------------------
OBJ_RADIUS = 22
BASE_FALL_SPEED = 230     # px/s at the very start
MAX_FALL_SPEED = 820      # hard cap so it stays humanly playable
BOMB_CHANCE = 0.18        # chance a new drop starts as a bomb
TRANSFORM_CHANCE = 0.22   # chance an apple will morph into a bomb mid-fall
CURVE_CHANCE = 0.55       # chance a drop follows a curved (deceptive) path

# ---- Basket (player) -------------------------------------------------------
basket_width = 120
basket_height = 70
basket_speed = 560        # px/s
basket_x = 0.0
basket_y = 0

# ---- Layout (recomputed on resize) ----------------------------------------
GROUND_Y = 0
background = None

# ---- Scenes ----------------------------------------------------------------
MENU, PLAYING, OVER = "menu", "playing", "over"
scene = MENU


# ----------------------------------------------------------------------------
#  Sound: synthesize an explosion into an in-memory WAV (no numpy needed).
# ----------------------------------------------------------------------------
def make_explosion_sound():
    if not HAS_AUDIO:
        return None
    try:
        sr = 44100
        dur = 0.9
        n = int(sr * dur)
        buf = io.BytesIO()
        w = wave.open(buf, "wb")
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = bytearray()
        rnd = random.Random(99)
        for i in range(n):
            t = i / sr
            noise = rnd.random() * 2.0 - 1.0
            noise_env = math.exp(-t * 6.0)
            rumble = (math.sin(2 * math.pi * 52 * t) * 0.6 +
                      math.sin(2 * math.pi * 38 * t) * 0.4)
            boom_env = math.exp(-t * 7.5)
            s = noise * 0.55 * noise_env + rumble * 0.7 * boom_env
            s = max(-1.0, min(1.0, s * 1.25))
            val = int(s * 32767 * 0.85)
            frames += struct.pack("<hh", val, val)
        w.writeframes(bytes(frames))
        w.close()
        buf.seek(0)
        return pygame.mixer.Sound(file=buf)
    except Exception:
        return None


explosion_sound = make_explosion_sound()


# ----------------------------------------------------------------------------
#  High score persistence
# ----------------------------------------------------------------------------
def load_highscore():
    try:
        with open(HIGHSCORE_FILE) as f:
            return int(f.read().strip() or "0")
    except Exception:
        return 0


def save_highscore(value):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(int(value)))
    except Exception:
        pass


high_score = load_highscore()


# ----------------------------------------------------------------------------
#  UI helpers
# ----------------------------------------------------------------------------
def draw_button(rect, text, font, mouse, base, hover, text_col=WHITE):
    hovered = rect.collidepoint(mouse)
    col = hover if hovered else base
    shadow = rect.move(0, 4)
    pygame.draw.rect(screen, (0, 0, 0, 60), shadow, border_radius=16)
    pygame.draw.rect(screen, col, rect, border_radius=16)
    pygame.draw.rect(screen, WHITE, rect, width=2, border_radius=16)
    label = font.render(text, True, text_col)
    screen.blit(label, label.get_rect(center=rect.center))


def text_center(text, font, cx, cy, color, shadow=True):
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        screen.blit(sh, sh.get_rect(center=(cx + 3, cy + 3)))
    img = font.render(text, True, color)
    screen.blit(img, img.get_rect(center=(cx, cy)))


def window_button_rects():
    size = 38
    y = 12
    max_btn = pygame.Rect(WIDTH - 2 * size - 20, y, size, size)
    min_btn = pygame.Rect(WIDTH - size - 12, y, size, size)
    return min_btn, max_btn


def draw_window_buttons(mouse):
    min_btn, max_btn = window_button_rects()
    for rect, kind in ((min_btn, "min"), (max_btn, "max")):
        hovered = rect.collidepoint(mouse)
        pygame.draw.rect(screen, (245, 245, 245) if hovered else (225, 225, 225),
                         rect, border_radius=8)
        pygame.draw.rect(screen, (90, 90, 90), rect, width=2, border_radius=8)
        cx, cy = rect.center
        if kind == "min":
            pygame.draw.line(screen, (40, 40, 40), (cx - 9, cy + 7), (cx + 9, cy + 7), 3)
        else:
            if is_fullscreen:  # "restore" glyph: two offset squares
                pygame.draw.rect(screen, (40, 40, 40), (cx - 5, cy - 8, 12, 12), 2)
                pygame.draw.rect(screen, (40, 40, 40), (cx - 9, cy - 4, 12, 12), 2)
            else:              # "maximize" glyph: single square
                pygame.draw.rect(screen, (40, 40, 40), (cx - 9, cy - 9, 18, 18), 2)
    return min_btn, max_btn


# ----------------------------------------------------------------------------
#  Background (forest) -- prebuilt once per size for performance
# ----------------------------------------------------------------------------
def draw_tree(surf, base_x, trunk_top_y, scale):
    trunk_w = max(10, int(26 * scale))
    trunk_h = GROUND_Y - trunk_top_y + 30
    pygame.draw.rect(surf, TRUNK, (base_x - trunk_w // 2, trunk_top_y, trunk_w, trunk_h))
    r = int(70 * scale)
    cx, cy = base_x, trunk_top_y - int(10 * scale)
    pygame.draw.circle(surf, LEAF_DARK, (cx, cy), r)
    pygame.draw.circle(surf, LEAF_DARK, (cx - int(r * 0.7), cy + int(r * 0.3)), int(r * 0.75))
    pygame.draw.circle(surf, LEAF_DARK, (cx + int(r * 0.7), cy + int(r * 0.3)), int(r * 0.75))
    pygame.draw.circle(surf, LEAF_MID,  (cx - int(r * 0.35), cy - int(r * 0.2)), int(r * 0.6))
    pygame.draw.circle(surf, LEAF_MID,  (cx + int(r * 0.4), cy - int(r * 0.1)), int(r * 0.55))
    pygame.draw.circle(surf, LEAF_LIGHT, (cx - int(r * 0.1), cy - int(r * 0.45)), int(r * 0.4))


def build_background():
    global background
    background = pygame.Surface((WIDTH, HEIGHT))

    # Sky gradient
    for y in range(GROUND_Y):
        t = y / max(1, GROUND_Y)
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
        pygame.draw.line(background, (r, g, b), (0, y), (WIDTH, y))

    # Sun
    sun_x = int(WIDTH * 0.16)
    pygame.draw.circle(background, (255, 241, 180), (sun_x, 130), 70)
    pygame.draw.circle(background, (255, 250, 215), (sun_x, 130), 48)

    # Clouds
    for fx, cy, s in [(0.7, 110, 1.0), (0.85, 190, 0.7), (0.47, 90, 0.6)]:
        cx = int(WIDTH * fx)
        for dx, dy, rr in [(-40, 10, 30), (0, 0, 42), (45, 12, 32), (90, 18, 26)]:
            pygame.draw.circle(background, (255, 255, 255),
                               (int(cx + dx * s), int(cy + dy * s)), int(rr * s))

    # Ground
    pygame.draw.rect(background, GRASS_DARK, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.rect(background, GRASS_LIGHT, (0, GROUND_Y, WIDTH, 46))

    # Trees spread across the full width (seeded for a stable layout)
    rnd = random.Random(7)
    x = 50
    while x < WIDTH + 80:
        draw_tree(background, x, rnd.randint(70, 150), rnd.uniform(0.85, 1.3))
        x += rnd.randint(120, 180)


# ----------------------------------------------------------------------------
#  Drawing the actors
# ----------------------------------------------------------------------------
def draw_apple(x, y):
    r = OBJ_RADIUS
    pygame.draw.circle(screen, APPLE_DARK, (x - r // 3, y + 2), r)
    pygame.draw.circle(screen, APPLE_DARK, (x + r // 3, y + 2), r)
    pygame.draw.circle(screen, APPLE_RED, (x - r // 3, y), r)
    pygame.draw.circle(screen, APPLE_RED, (x + r // 3, y), r)
    pygame.draw.circle(screen, APPLE_RED, (x, y + r // 4), r)
    pygame.draw.circle(screen, APPLE_SHINE, (x - r // 2, y - r // 2), max(3, r // 5))
    pygame.draw.line(screen, STEM_BROWN, (x, y - r + 2), (x + 4, y - r - 10), 5)
    leaf = [(x + 4, y - r - 8), (x + 20, y - r - 16), (x + 12, y - r - 2)]
    pygame.draw.polygon(screen, LEAF_GREEN, leaf)


def draw_bomb(x, y, t):
    r = OBJ_RADIUS
    pygame.draw.circle(screen, BOMB_BLACK, (x, y + 2), r)
    pygame.draw.circle(screen, BOMB_GRAY, (x - r // 3, y - r // 3), max(3, r // 4))
    pygame.draw.rect(screen, BOMB_GRAY, (x - 6, y - r - 6, 12, 10), border_radius=3)
    pygame.draw.line(screen, FUSE_BROWN, (x, y - r - 4), (x + 8, y - r - 16), 4)
    pygame.draw.line(screen, FUSE_BROWN, (x + 8, y - r - 16), (x + 2, y - r - 26), 4)
    flick = 3 + int(3 * abs(math.sin(t * 12)))
    pygame.draw.circle(screen, SPARK, (x + 2, y - r - 28), flick)
    pygame.draw.circle(screen, WHITE, (x + 2, y - r - 28), max(1, flick // 2))


def draw_basket(x, y):
    w, h = basket_width, basket_height
    rim_h = 16
    pygame.draw.polygon(screen, (150, 95, 45),
                        [(x + 6, y + rim_h), (x + w - 6, y + rim_h),
                         (x + w - 16, y + h), (x + 16, y + h)])
    for i in range(1, 5):
        yy = y + rim_h + i * (h - rim_h) // 5
        pygame.draw.line(screen, (110, 66, 30), (x + 10 + i, yy), (x + w - 10 - i, yy), 2)
    for i in range(1, 6):
        xx = x + 12 + i * (w - 24) // 6
        pygame.draw.line(screen, (120, 72, 34), (xx, y + rim_h + 2), (xx, y + h - 2), 2)
    pygame.draw.rect(screen, (175, 115, 60), (x, y, w, rim_h), border_radius=8)
    pygame.draw.rect(screen, (120, 72, 34), (x, y, w, rim_h), width=3, border_radius=8)


# ----------------------------------------------------------------------------
#  Game state
# ----------------------------------------------------------------------------
def setup_layout():
    global GROUND_Y, basket_y
    GROUND_Y = HEIGHT - max(90, int(HEIGHT * 0.14))
    basket_y = GROUND_Y - basket_height + 20


def spawn_object():
    """Create a new falling object with curve / transform behaviour."""
    is_bomb = random.random() < BOMB_CHANCE
    curved = random.random() < CURVE_CHANCE
    amp = random.randint(55, 110) if curved else 0
    base_x = random.randint(OBJ_RADIUS + 4 + amp, WIDTH - OBJ_RADIUS - 4 - amp)
    base_x = max(OBJ_RADIUS + 4, min(WIDTH - OBJ_RADIUS - 4, base_x))
    will_transform = (not is_bomb) and (random.random() < TRANSFORM_CHANCE)
    return {
        "base_x": base_x,
        "x": base_x,
        "y": -OBJ_RADIUS,
        "bomb": is_bomb,
        "amp": amp,
        "freq": random.uniform(0.012, 0.024),
        "phase": random.uniform(0, math.tau),
        "transform_at": random.uniform(HEIGHT * 0.35, HEIGHT * 0.7) if will_transform else None,
    }


def new_game_state():
    return {
        "score": 0,
        "missed": 0,
        "obj": spawn_object(),
        "fall_speed": BASE_FALL_SPEED,
        "time": 0.0,
        "blast": None,      # explosion animation {x, y, t, parts}
        "new_high": False,
    }


def make_blast(x, y):
    parts = []
    for _ in range(26):
        ang = random.uniform(0, math.tau)
        spd = random.uniform(140, 420)
        col = random.choice([(255, 170, 40), (255, 90, 40), (90, 90, 90),
                             (255, 220, 120), (60, 60, 60)])
        parts.append({"ang": ang, "spd": spd, "r": random.randint(4, 10), "col": col})
    if explosion_sound:
        explosion_sound.play()
    return {"x": x, "y": y, "t": 0.0, "parts": parts}


def draw_blast(blast):
    t = blast["t"]
    cx, cy = blast["x"], blast["y"]
    # Central flash
    flash_r = int(30 + 260 * min(1.0, t / 0.5))
    alpha = max(0, 220 - int(300 * t))
    if alpha > 0:
        surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 180, 60, alpha), (flash_r, flash_r), flash_r)
        pygame.draw.circle(surf, (255, 240, 180, min(255, alpha + 40)),
                           (flash_r, flash_r), flash_r // 2)
        screen.blit(surf, (cx - flash_r, cy - flash_r))
    # Flying debris
    for p in blast["parts"]:
        px = cx + math.cos(p["ang"]) * p["spd"] * t
        py = cy + math.sin(p["ang"]) * p["spd"] * t + 120 * t * t
        rr = max(1, int(p["r"] * (1.0 - t)))
        if rr > 0:
            pygame.draw.circle(screen, p["col"], (int(px), int(py)), rr)


def apply_display_mode():
    """(Re)create the window surface and rebuild layout/background."""
    global screen, WIDTH, HEIGHT, basket_x
    if is_fullscreen:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WINDOWED_W, WINDOWED_H), pygame.RESIZABLE)
    WIDTH, HEIGHT = screen.get_size()
    setup_layout()
    build_background()
    basket_x = max(0, min(WIDTH - basket_width, basket_x))


def toggle_fullscreen():
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    apply_display_mode()


def center_basket():
    global basket_x
    basket_x = WIDTH / 2 - basket_width / 2


# ---- Initial setup ---------------------------------------------------------
setup_layout()
build_background()
center_basket()
state = new_game_state()


# ----------------------------------------------------------------------------
#  Scene drawing
# ----------------------------------------------------------------------------
def draw_menu(mouse):
    screen.blit(background, (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 70))
    screen.blit(overlay, (0, 0))

    cx = WIDTH // 2
    text_center("APPLE CATCHER", font_title, cx, int(HEIGHT * 0.22), (255, 236, 140))
    text_center("Catch apples - dodge bombs", font_small, cx, int(HEIGHT * 0.30),
                (235, 235, 235))

    # decorative apple + bomb
    draw_apple(cx - 150, int(HEIGHT * 0.22))
    draw_bomb(cx + 150, int(HEIGHT * 0.22), pygame.time.get_ticks() / 1000.0)

    play_btn = pygame.Rect(0, 0, 300, 70)
    play_btn.center = (cx, int(HEIGHT * 0.46))
    quit_btn = pygame.Rect(0, 0, 300, 64)
    quit_btn.center = (cx, int(HEIGHT * 0.57))
    draw_button(play_btn, "NEW GAME", font_mid, mouse, (60, 150, 70), (80, 185, 90))
    draw_button(quit_btn, "QUIT", font_small, mouse, (120, 60, 60), (160, 80, 80))

    # High score panel
    hs_rect = pygame.Rect(0, 0, 340, 90)
    hs_rect.center = (cx, int(HEIGHT * 0.70))
    pygame.draw.rect(screen, (0, 0, 0, 120), hs_rect, border_radius=14)
    pygame.draw.rect(screen, GOLD, hs_rect, width=3, border_radius=14)
    text_center("HIGH SCORE", font_tiny, cx, hs_rect.top + 26, GOLD, shadow=False)
    text_center(str(high_score), font_big, cx, hs_rect.top + 60, WHITE)

    text_center("Move:  <-  ->   or   A  D", font_tiny, cx, int(HEIGHT * 0.82),
                (230, 230, 230))
    return play_btn, quit_btn


def draw_game(mouse):
    screen.blit(background, (0, 0))
    obj = state["obj"]

    if state["blast"] is None:
        if obj["bomb"]:
            draw_bomb(int(obj["x"]), int(obj["y"]), state["time"])
        else:
            draw_apple(int(obj["x"]), int(obj["y"]))

    draw_basket(int(basket_x), basket_y)

    if state["blast"] is not None:
        draw_blast(state["blast"])

    # HUD
    hud = font_small.render(f"Apples: {state['score']}", True, WHITE)
    sh = font_small.render(f"Apples: {state['score']}", True, BLACK)
    screen.blit(sh, (22, 20)); screen.blit(hud, (20, 18))
    best = font_tiny.render(f"Best: {high_score}", True, GOLD)
    screen.blit(best, (20, 56))
    missed = font_tiny.render(f"Missed: {state['missed']}", True, (255, 210, 210))
    screen.blit(missed, (20, 84))


def draw_over(mouse):
    # Keep the forest + a frozen basket behind the panel
    screen.blit(background, (0, 0))
    draw_basket(int(basket_x), basket_y)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    cx = WIDTH // 2
    panel = pygame.Rect(0, 0, 460, 440)
    panel.center = (cx, HEIGHT // 2)
    pygame.draw.rect(screen, PANEL_BG, panel, border_radius=24)
    pygame.draw.rect(screen, ACCENT, panel, width=3, border_radius=24)

    text_center("GAME OVER", font_big, cx, panel.top + 60, ACCENT)

    if state["new_high"]:
        badge = pygame.Rect(0, 0, 280, 40)
        badge.center = (cx, panel.top + 110)
        pygame.draw.rect(screen, GOLD, badge, border_radius=20)
        text_center("NEW HIGH SCORE!", font_tiny, cx, badge.centery, (60, 45, 0),
                    shadow=False)

    text_center("Apples caught", font_small, cx, panel.top + 160, (210, 210, 210),
                shadow=False)
    text_center(str(state["score"]), font_title, cx, panel.top + 210, WHITE)
    text_center(f"Best: {high_score}", font_small, cx, panel.top + 262, GOLD,
                shadow=False)

    again_btn = pygame.Rect(0, 0, 360, 60)
    again_btn.center = (cx, panel.top + 330)
    menu_btn = pygame.Rect(0, 0, 360, 56)
    menu_btn.center = (cx, panel.top + 398)
    draw_button(again_btn, "PLAY AGAIN", font_mid, mouse, (60, 150, 70), (80, 185, 90))
    draw_button(menu_btn, "MAIN MENU", font_small, mouse, (70, 90, 120), (90, 115, 155))
    return again_btn, menu_btn


# ----------------------------------------------------------------------------
#  Game-logic update
# ----------------------------------------------------------------------------
def update_game(dt, keys):
    global basket_x, high_score, scene
    state["time"] += dt

    # Explosion in progress: run the animation, then end the game.
    if state["blast"] is not None:
        state["blast"]["t"] += dt
        if state["blast"]["t"] > 0.85:
            if state["score"] > high_score:
                high_score = state["score"]
                state["new_high"] = True
                save_highscore(high_score)
            scene = OVER
        return

    # Move basket
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
        basket_x -= basket_speed * dt
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
        basket_x += basket_speed * dt
    basket_x = max(0, min(WIDTH - basket_width, basket_x))

    # Difficulty ramps with both time survived and apples caught (capped).
    state["fall_speed"] = min(MAX_FALL_SPEED,
                              BASE_FALL_SPEED + state["time"] * 7 + state["score"] * 9)

    obj = state["obj"]
    obj["y"] += state["fall_speed"] * dt

    # Deceptive curved horizontal motion
    if obj["amp"]:
        obj["x"] = obj["base_x"] + obj["amp"] * math.sin(obj["freq"] * obj["y"] + obj["phase"])
        obj["x"] = max(OBJ_RADIUS, min(WIDTH - OBJ_RADIUS, obj["x"]))
    else:
        obj["x"] = obj["base_x"]

    # Mid-fall apple -> bomb transformation
    if obj["transform_at"] is not None and not obj["bomb"] and obj["y"] >= obj["transform_at"]:
        obj["bomb"] = True
        obj["transform_at"] = None

    # Catch test (catch zone sits just inside the basket rim)
    catch = pygame.Rect(basket_x + 10, basket_y + 6, basket_width - 20, 42)
    obj_rect = pygame.Rect(obj["x"] - OBJ_RADIUS, obj["y"] - OBJ_RADIUS,
                           OBJ_RADIUS * 2, OBJ_RADIUS * 2)

    if obj_rect.colliderect(catch):
        if obj["bomb"]:
            state["blast"] = make_blast(int(obj["x"]), int(obj["y"]))
        else:
            state["score"] += 1
            state["obj"] = spawn_object()
    elif obj["y"] - OBJ_RADIUS > HEIGHT:
        if not obj["bomb"]:
            state["missed"] += 1
        state["obj"] = spawn_object()


def start_new_game():
    global state, scene
    state = new_game_state()
    center_basket()
    scene = PLAYING


# ----------------------------------------------------------------------------
#  Main loop
# ----------------------------------------------------------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    mouse = pygame.mouse.get_pos()

    # Layout for clickable UI this frame
    min_btn, max_btn = window_button_rects()
    menu_play = menu_quit = over_again = over_menu = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
            WINDOWED_W, WINDOWED_H = max(640, event.w), max(560, event.h)
            apply_display_mode()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if is_fullscreen:
                    toggle_fullscreen()
                elif scene == PLAYING or scene == OVER:
                    scene = MENU
                else:
                    running = False
            elif event.key == pygame.K_F11:
                toggle_fullscreen()
            elif scene == OVER:
                if event.key == pygame.K_r:
                    start_new_game()
                elif event.key == pygame.K_m:
                    scene = MENU
            elif scene == MENU and event.key == pygame.K_RETURN:
                start_new_game()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if min_btn.collidepoint(pos):
                pygame.display.iconify()
            elif max_btn.collidepoint(pos):
                toggle_fullscreen()
            elif scene == MENU:
                # Rects recomputed below for drawing; recompute here too
                cx = WIDTH // 2
                pb = pygame.Rect(0, 0, 300, 70); pb.center = (cx, int(HEIGHT * 0.46))
                qb = pygame.Rect(0, 0, 300, 64); qb.center = (cx, int(HEIGHT * 0.57))
                if pb.collidepoint(pos):
                    start_new_game()
                elif qb.collidepoint(pos):
                    running = False
            elif scene == OVER:
                cx = WIDTH // 2
                panel_top = HEIGHT // 2 - 220
                ab = pygame.Rect(0, 0, 360, 60); ab.center = (cx, panel_top + 330)
                mb = pygame.Rect(0, 0, 360, 56); mb.center = (cx, panel_top + 398)
                if ab.collidepoint(pos):
                    start_new_game()
                elif mb.collidepoint(pos):
                    scene = MENU

    keys = pygame.key.get_pressed()
    if scene == PLAYING:
        update_game(dt, keys)

    # ---- Draw ----
    if scene == MENU:
        draw_menu(mouse)
    elif scene == PLAYING:
        draw_game(mouse)
    else:
        draw_over(mouse)

    draw_window_buttons(mouse)
    pygame.display.update()

pygame.quit()
