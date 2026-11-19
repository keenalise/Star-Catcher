import pygame
import random
import math

# ----------------------------------------------------------------------------
#  Apple Catcher  (forest edition)
#  - Apples fall from the trees; move the basket to catch them.
#  - Every so often a bomb drops instead. Catch it and the game is over!
# ----------------------------------------------------------------------------

pygame.init()

# Screen dimensions
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Apple Catcher")
clock = pygame.time.Clock()
FPS = 60

GROUND_Y = SCREEN_HEIGHT - 110  # top of the grass strip

# ---- Colors ----------------------------------------------------------------
WHITE       = (255, 255, 255)
BLACK       = (0, 0, 0)
SKY_TOP     = (135, 206, 250)
SKY_BOTTOM  = (215, 240, 220)
GRASS_LIGHT = (104, 176, 66)
GRASS_DARK  = (70, 132, 44)
TRUNK       = (101, 67, 33)
LEAF_DARK   = (34, 110, 44)
LEAF_MID    = (52, 140, 58)
LEAF_LIGHT  = (96, 178, 72)
APPLE_RED   = (210, 40, 40)
APPLE_SHINE = (255, 170, 160)
STEM_BROWN  = (92, 60, 30)
LEAF_GREEN  = (80, 170, 70)
BOMB_BLACK  = (30, 30, 34)
BOMB_GRAY   = (90, 90, 100)
FUSE_BROWN  = (120, 80, 40)
SPARK       = (255, 200, 60)

# ---- Fonts -----------------------------------------------------------------
font_big   = pygame.font.SysFont("arialrounded,arial", 72, bold=True)
font_mid   = pygame.font.SysFont("arialrounded,arial", 44, bold=True)
font_small = pygame.font.SysFont("arialrounded,arial", 30, bold=True)

# ---- Basket (player) -------------------------------------------------------
basket_width = 120
basket_height = 70
basket_x = SCREEN_WIDTH // 2 - basket_width // 2
basket_y = GROUND_Y - basket_height + 20
basket_speed = 520  # pixels per second

# ---- Falling-object settings ----------------------------------------------
OBJ_RADIUS = 22
BASE_FALL_SPEED = 240   # px/s at the start
BOMB_CHANCE = 0.22      # probability a new drop is a bomb

# Pre-build a static background so we don't redraw trees every frame.
background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))


def build_background():
    # Sky gradient
    for y in range(GROUND_Y):
        t = y / GROUND_Y
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
        pygame.draw.line(background, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Soft sun
    pygame.draw.circle(background, (255, 241, 180), (150, 130), 70)
    pygame.draw.circle(background, (255, 250, 215), (150, 130), 48)

    # A few drifting clouds
    for cx, cy, s in [(640, 110, 1.0), (770, 190, 0.7), (430, 90, 0.6)]:
        for dx, dy, rr in [(-40, 10, 30), (0, 0, 42), (45, 12, 32), (90, 18, 26)]:
            pygame.draw.circle(background, (255, 255, 255),
                               (int(cx + dx * s), int(cy + dy * s)), int(rr * s))

    # Grass ground
    pygame.draw.rect(background, GRASS_DARK, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
    pygame.draw.rect(background, GRASS_LIGHT, (0, GROUND_Y, SCREEN_WIDTH, 46))

    # Layered trees across the top for a forest feel
    tree_spots = [60, 230, 400, 560, 720, 850, 150, 320, 640]
    random.seed(7)  # fixed layout each run
    for base_x in tree_spots:
        draw_tree(background, base_x, random.randint(70, 150), random.uniform(0.8, 1.3))
    random.seed()  # restore randomness for gameplay


def draw_tree(surf, base_x, trunk_top_y, scale):
    trunk_w = int(26 * scale)
    trunk_h = GROUND_Y - trunk_top_y + 30
    pygame.draw.rect(surf, TRUNK, (base_x - trunk_w // 2, trunk_top_y, trunk_w, trunk_h))
    # Foliage: overlapping circles in three greens
    r = int(70 * scale)
    cx, cy = base_x, trunk_top_y - int(10 * scale)
    pygame.draw.circle(surf, LEAF_DARK, (cx, cy), r)
    pygame.draw.circle(surf, LEAF_DARK, (cx - int(r * 0.7), cy + int(r * 0.3)), int(r * 0.75))
    pygame.draw.circle(surf, LEAF_DARK, (cx + int(r * 0.7), cy + int(r * 0.3)), int(r * 0.75))
    pygame.draw.circle(surf, LEAF_MID,  (cx - int(r * 0.35), cy - int(r * 0.2)), int(r * 0.6))
    pygame.draw.circle(surf, LEAF_MID,  (cx + int(r * 0.4), cy - int(r * 0.1)), int(r * 0.55))
    pygame.draw.circle(surf, LEAF_LIGHT, (cx - int(r * 0.1), cy - int(r * 0.45)), int(r * 0.4))


def draw_apple(x, y):
    """Draw an apple centered at (x, y)."""
    r = OBJ_RADIUS
    # Body: two lobes + fill for a classic apple silhouette
    pygame.draw.circle(screen, APPLE_RED, (x - r // 3, y), r)
    pygame.draw.circle(screen, APPLE_RED, (x + r // 3, y), r)
    pygame.draw.circle(screen, APPLE_RED, (x, y + r // 4), r)
    # Shine
    pygame.draw.circle(screen, APPLE_SHINE, (x - r // 2, y - r // 2), max(3, r // 5))
    # Stem
    pygame.draw.line(screen, STEM_BROWN, (x, y - r + 2), (x + 4, y - r - 10), 5)
    # Leaf
    leaf = [(x + 4, y - r - 8), (x + 20, y - r - 16), (x + 12, y - r - 2)]
    pygame.draw.polygon(screen, LEAF_GREEN, leaf)


def draw_bomb(x, y, t):
    """Draw a bomb centered at (x, y). t drives the fuse sparkle."""
    r = OBJ_RADIUS
    pygame.draw.circle(screen, BOMB_BLACK, (x, y + 2), r)
    pygame.draw.circle(screen, BOMB_GRAY, (x - r // 3, y - r // 3), max(3, r // 4))  # highlight
    # Fuse cap
    pygame.draw.rect(screen, BOMB_GRAY, (x - 6, y - r - 6, 12, 10), border_radius=3)
    # Curvy fuse
    pygame.draw.line(screen, FUSE_BROWN, (x, y - r - 4), (x + 8, y - r - 16), 4)
    pygame.draw.line(screen, FUSE_BROWN, (x + 8, y - r - 16), (x + 2, y - r - 26), 4)
    # Sparkle
    flick = 3 + int(3 * abs(math.sin(t * 12)))
    pygame.draw.circle(screen, SPARK, (x + 2, y - r - 28), flick)
    pygame.draw.circle(screen, WHITE, (x + 2, y - r - 28), max(1, flick // 2))


def draw_basket(x, y):
    """Draw a wicker basket with its top-left corner near (x, y)."""
    w, h = basket_width, basket_height
    rim_h = 16
    body = pygame.Rect(x, y + rim_h, w, h - rim_h)
    # Basket body (tapered look via polygon)
    pygame.draw.polygon(screen, (150, 95, 45),
                        [(x + 6, y + rim_h), (x + w - 6, y + rim_h),
                         (x + w - 16, y + h), (x + 16, y + h)])
    # Weave lines
    for i in range(1, 5):
        yy = y + rim_h + i * (h - rim_h) // 5
        pygame.draw.line(screen, (110, 66, 30),
                         (x + 10 + i, yy), (x + w - 10 - i, yy), 2)
    for i in range(1, 6):
        xx = x + 12 + i * (w - 24) // 6
        pygame.draw.line(screen, (120, 72, 34),
                         (xx, y + rim_h + 2), (xx, y + h - 2), 2)
    # Rim
    pygame.draw.rect(screen, (175, 115, 60), (x, y, w, rim_h), border_radius=8)
    pygame.draw.rect(screen, (120, 72, 34), (x, y, w, rim_h), width=3, border_radius=8)
    return pygame.Rect(x, y, w, h)


def spawn_object():
    """Return a new falling object dict (apple or bomb)."""
    is_bomb = random.random() < BOMB_CHANCE
    return {
        "x": random.randint(OBJ_RADIUS + 4, SCREEN_WIDTH - OBJ_RADIUS - 4),
        "y": -OBJ_RADIUS,
        "bomb": is_bomb,
    }


def reset_game():
    return {
        "score": 0,
        "missed": 0,
        "obj": spawn_object(),
        "fall_speed": BASE_FALL_SPEED,
        "over": False,
        "time": 0.0,
    }


build_background()
state = reset_game()

# Center basket at start
basket_x = SCREEN_WIDTH // 2 - basket_width // 2

running = True
while running:
    dt = clock.tick(FPS) / 1000.0  # seconds since last frame
    state["time"] += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if state["over"] and event.key == pygame.K_r:
                state = reset_game()
                basket_x = SCREEN_WIDTH // 2 - basket_width // 2

    keys = pygame.key.get_pressed()

    if not state["over"]:
        # --- Move basket (arrow keys or A/D) ---
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and basket_x > 0:
            basket_x -= basket_speed * dt
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and basket_x < SCREEN_WIDTH - basket_width:
            basket_x += basket_speed * dt
        basket_x = max(0, min(SCREEN_WIDTH - basket_width, basket_x))

        # --- Move the falling object ---
        obj = state["obj"]
        obj["y"] += state["fall_speed"] * dt

        # Basket catch area (a bit inside the rim so it feels fair)
        catch = pygame.Rect(basket_x + 10, basket_y + 6,
                            basket_width - 20, 40)
        obj_rect = pygame.Rect(obj["x"] - OBJ_RADIUS, obj["y"] - OBJ_RADIUS,
                               OBJ_RADIUS * 2, OBJ_RADIUS * 2)

        if obj_rect.colliderect(catch):
            if obj["bomb"]:
                state["over"] = True
            else:
                state["score"] += 1
                # Speed up a touch every few apples
                state["fall_speed"] = BASE_FALL_SPEED + state["score"] * 6
                state["obj"] = spawn_object()
        elif obj["y"] - OBJ_RADIUS > SCREEN_HEIGHT:
            if not obj["bomb"]:
                state["missed"] += 1
            state["obj"] = spawn_object()

    # --- Draw ---
    screen.blit(background, (0, 0))

    obj = state["obj"]
    if obj["bomb"]:
        draw_bomb(int(obj["x"]), int(obj["y"]), state["time"])
    else:
        draw_apple(int(obj["x"]), int(obj["y"]))

    draw_basket(int(basket_x), basket_y)

    # HUD
    score_text = font_small.render(f"Apples: {state['score']}", True, BLACK)
    screen.blit(score_text, (20, 18))
    missed_text = font_small.render(f"Missed: {state['missed']}", True, (120, 30, 30))
    screen.blit(missed_text, (20, 54))

    if state["over"]:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        go = font_big.render("BOOM! Game Over", True, (255, 90, 90))
        screen.blit(go, go.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70)))

        sc = font_mid.render(f"Apples caught: {state['score']}", True, WHITE)
        screen.blit(sc, sc.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)))

        tip = font_small.render("Press  R  to play again    -    Esc to quit", True, (230, 230, 230))
        screen.blit(tip, tip.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)))

    pygame.display.update()

pygame.quit()
