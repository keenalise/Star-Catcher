"""Central configuration: paths, tunables, colours, and strings.

Everything a designer might want to tweak lives here so the rest of the code
reads like intent rather than magic numbers.
"""
import os

# --- Paths ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")

# --- Window -----------------------------------------------------------------
WINDOW_W, WINDOW_H = 960, 820
MIN_W, MIN_H = 720, 640
FPS = 60
GROUND_FRAC = 0.82          # ground line as a fraction of window height
TITLE = "Apple Catcher"

# --- Falling objects --------------------------------------------------------
OBJ_SIZE = 66               # on-screen size of apples/bombs/power-ups (px)
BASE_FALL_SPEED = 240       # px/s at the start of a run
MAX_FALL_SPEED = 830        # capped so it stays playable
SPEED_BY_TIME = 7           # +px/s per second survived
SPEED_BY_SCORE = 9          # +px/s per apple caught

# Spawn probabilities for each new drop (apple fills the remainder)
P_SHIELD = 0.05
P_EXTEND = 0.05
P_BOMB = 0.18
# Chance a falling apple/bomb morphs into the other type mid-fall
TRANSFORM_CHANCE = 0.30
# Chance a drop follows a curved (deceptive) horizontal path
CURVE_CHANCE = 0.55
CURVE_AMP = (55, 115)       # min/max sideways swing in px

# --- Basket -----------------------------------------------------------------
BASKET_BASE_W = 150
BASKET_EXTEND_W = 250
BASKET_H = 92
BASKET_SPEED = 560          # px/s
BOOST_MULT = 1.9            # speed multiplier while boosting
DOUBLE_TAP = 0.30           # max seconds between taps to trigger a boost

# --- Lives & power-up durations (seconds) -----------------------------------
START_LIVES = 3
SHIELD_TIME = 15.0
EXTEND_TIME = 9.0
BOOST_TIME = 3.0

# --- "Watch ad to continue" -------------------------------------------------
AD_UNLOCK_TIME = 10.0       # seconds before Continue unlocks
AD_URLS = [
    "https://youtu.be/zd4GXZUibyA",
    "https://youtu.be/GxMUrEHfB54",
]

# --- Colours ----------------------------------------------------------------
WHITE      = (255, 255, 255)
BLACK      = (18, 18, 22)
PANEL_BG   = (26, 32, 30)
PANEL_EDGE = (235, 70, 60)
ACCENT     = (235, 70, 60)
GREEN      = (60, 150, 70)
GREEN_HI   = (80, 185, 90)
BLUE       = (70, 100, 150)
BLUE_HI    = (92, 128, 185)
GOLD       = (255, 205, 70)
RED_SOFT   = (255, 120, 110)
SHIELD_CLR = (90, 170, 255)
EXTEND_CLR = (70, 210, 200)
BOOST_CLR  = (255, 170, 60)
