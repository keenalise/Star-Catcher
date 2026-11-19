"""The Game class: window management, scenes, input, update and render."""
import random
import webbrowser

import pygame

from . import settings as S
from . import ui
from .assets import Assets
from .audio import Audio
from .effects import Blast
from .entities import FallingObject, Basket, APPLE, BOMB, SHIELD, EXTEND, HEART
from .storage import load_highscore, save_highscore

MENU, PLAYING, OVER, HELP = "menu", "playing", "over", "help"


class Game:
    def __init__(self):
        pygame.init()
        self.windowed = (S.WINDOW_W, S.WINDOW_H)
        self.width, self.height = self.windowed
        self.is_fullscreen = False
        self.screen = pygame.display.set_mode(self.windowed, pygame.RESIZABLE)
        pygame.display.set_caption(S.TITLE)

        self.assets = Assets()
        pygame.display.set_icon(self.assets.window_icon())
        self.audio = Audio()
        self.clock = pygame.time.Clock()

        self.high_score = load_highscore()
        self.scene = MENU
        self.now = 0.0

        # buttons (positioned each frame by _layout)
        self.btn_play = ui.Button("NEW GAME", self.assets.font_mid, S.GREEN, S.GREEN_HI)
        self.btn_help = ui.Button("HOW TO PLAY", self.assets.font_small, S.BLUE, S.BLUE_HI)
        self.btn_quit = ui.Button("QUIT", self.assets.font_small, (120, 60, 60), (160, 80, 80))
        self.btn_back = ui.Button("BACK", self.assets.font_small, S.BLUE, S.BLUE_HI)
        self.btn_again = ui.Button("PLAY AGAIN", self.assets.font_mid, S.GREEN, S.GREEN_HI)
        self.btn_menu = ui.Button("MAIN MENU", self.assets.font_small, S.BLUE, S.BLUE_HI)
        self.btn_ad = ui.Button("WATCH AD TO CONTINUE", self.assets.font_small,
                                (200, 120, 40), (230, 150, 60))

        # double-tap tracking
        self.last_tap_dir = 0
        self.last_tap_time = -1.0

        self.basket = Basket(self.width)
        self._menu_decor = self._make_menu_decor()
        self._reset_run()

    # --- layout helpers -----------------------------------------------------
    @property
    def ground_y(self):
        return int(self.height * S.GROUND_FRAC)

    @property
    def basket_y(self):
        return self.ground_y - self.basket.h + 18

    def _make_menu_decor(self):
        decor = []
        for _ in range(7):
            decor.append({
                "x": random.uniform(0, S.WINDOW_W),
                "y": random.uniform(-200, S.WINDOW_H),
                "spd": random.uniform(40, 90),
                "size": random.randint(34, 60),
                "kind": random.choice([APPLE, APPLE, APPLE, BOMB]),
            })
        return decor

    # --- run lifecycle ------------------------------------------------------
    def _reset_run(self):
        self.score = 0
        self.lives = S.START_LIVES
        self.timers = {"shield": 0.0, "extend": 0.0, "boost": 0.0}
        self.speed = S.BASE_FALL_SPEED
        self.run_time = 0.0
        self.obj = FallingObject(self.width, self.height)
        self.blast = None
        self.dying = False
        self.over_reason = None
        self.new_high = False
        self.ad_active = False
        self.ad_elapsed = 0.0
        self.ad_unlocked = False
        self.basket.set_extended(False, self.width)
        self.basket.center_in(self.width)

    def start_new_game(self):
        self._reset_run()
        self.scene = PLAYING

    def continue_after_ad(self):
        """Revive the player after they watch an ad."""
        self.lives = S.START_LIVES
        self.timers = {"shield": 0.0, "extend": 0.0, "boost": 0.0}
        self.blast = None
        self.dying = False
        self.ad_active = False
        self.ad_elapsed = 0.0
        self.ad_unlocked = False
        self.obj = FallingObject(self.width, self.height)
        self.basket.set_extended(False, self.width)
        self.basket.center_in(self.width)
        self.scene = PLAYING

    def finalize_game_over(self, reason):
        self.over_reason = reason
        if self.score > self.high_score:
            self.high_score = self.score
            self.new_high = True
            save_highscore(self.high_score)
        self.ad_active = False
        self.ad_elapsed = 0.0
        self.ad_unlocked = False
        self.scene = OVER

    # --- display mode -------------------------------------------------------
    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            # (0, 0) tells SDL to use the full desktop resolution. Querying
            # display.Info() here would return the *window* size, not the
            # desktop, which left the screen only partly painted.
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed, pygame.RESIZABLE)
        self.width, self.height = self.screen.get_size()
        self.basket.clamp(self.width)

    def on_resize(self, w, h):
        self.windowed = (max(S.MIN_W, w), max(S.MIN_H, h))
        self.screen = pygame.display.set_mode(self.windowed, pygame.RESIZABLE)
        self.width, self.height = self.screen.get_size()
        self.basket.clamp(self.width)

    # --- boost (double-tap) -------------------------------------------------
    def _handle_tap(self, direction):
        if direction == self.last_tap_dir and (self.now - self.last_tap_time) <= S.DOUBLE_TAP:
            self.timers["boost"] = S.BOOST_TIME
            self.last_tap_dir = 0  # consume so a triple-tap doesn't re-trigger
        else:
            self.last_tap_dir = direction
            self.last_tap_time = self.now

    # --- events -------------------------------------------------------------
    def handle_events(self):
        mouse = pygame.mouse.get_pos()
        min_btn, max_btn = ui.window_button_rects(self.width)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                self.on_resize(event.w, event.h)

            elif event.type == pygame.KEYDOWN:
                if not self._on_key(event):
                    return False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if min_btn.collidepoint(pos):
                    pygame.display.iconify()
                elif max_btn.collidepoint(pos):
                    self.toggle_fullscreen()
                elif not self._on_click(pos):
                    return False
        return True

    def _on_key(self, event):
        key = event.key
        if key == pygame.K_ESCAPE:
            if self.is_fullscreen:
                self.toggle_fullscreen()
            elif self.scene in (PLAYING, OVER, HELP):
                self.scene = MENU
            else:
                return False
        elif key == pygame.K_F11:
            self.toggle_fullscreen()
        elif self.scene == PLAYING:
            if key in (pygame.K_LEFT, pygame.K_a):
                self._handle_tap(-1)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self._handle_tap(1)
        elif self.scene == MENU:
            if key == pygame.K_RETURN:
                self.start_new_game()
            elif key == pygame.K_h:
                self.scene = HELP
        elif self.scene == OVER:
            if key == pygame.K_r:
                self.start_new_game()
            elif key == pygame.K_m:
                self.scene = MENU
            elif key == pygame.K_c and self.ad_unlocked:
                self.continue_after_ad()
        return True

    def _on_click(self, pos):
        if self.scene == MENU:
            if self.btn_play.hit(pos):
                self.start_new_game()
            elif self.btn_help.hit(pos):
                self.scene = HELP
            elif self.btn_quit.hit(pos):
                return False
        elif self.scene == HELP:
            if self.btn_back.hit(pos):
                self.scene = MENU
        elif self.scene == OVER:
            if self.btn_again.hit(pos):
                self.start_new_game()
            elif self.btn_menu.hit(pos):
                self.scene = MENU
            elif self.btn_ad.hit(pos):
                self._ad_button_pressed()
        return True

    def _ad_button_pressed(self):
        if self.ad_unlocked:
            self.continue_after_ad()
        elif not self.ad_active:
            self.ad_active = True
            self.ad_elapsed = 0.0
            try:
                webbrowser.open(random.choice(S.AD_URLS))
            except Exception:
                pass

    # --- update -------------------------------------------------------------
    def update(self, dt):
        self.now += dt
        if self.scene in (MENU, HELP):
            self._update_menu(dt)
        elif self.scene == PLAYING:
            self._update_play(dt)
        elif self.scene == OVER and self.ad_active and not self.ad_unlocked:
            self.ad_elapsed += dt
            if self.ad_elapsed >= S.AD_UNLOCK_TIME:
                self.ad_unlocked = True

    def _update_menu(self, dt):
        for d in self._menu_decor:
            d["y"] += d["spd"] * dt
            if d["y"] - d["size"] > self.height:
                d["y"] = -d["size"]
                d["x"] = random.uniform(0, self.width)
                d["kind"] = random.choice([APPLE, APPLE, APPLE, BOMB])

    def _update_play(self, dt):
        # explosion death sequence
        if self.dying:
            if self.blast:
                self.blast.update(dt)
                if self.blast.done:
                    self.finalize_game_over("bomb")
            return

        # tick power-up timers
        for key in self.timers:
            if self.timers[key] > 0:
                self.timers[key] = max(0.0, self.timers[key] - dt)
        if self.timers["extend"] == 0 and self.basket.extended:
            self.basket.set_extended(False, self.width)

        # move basket (with optional boost)
        mult = S.BOOST_MULT if self.timers["boost"] > 0 else 1.0
        keys = pygame.key.get_pressed()
        self.basket.update(dt, keys, self.width, mult)

        # difficulty ramp
        self.run_time += dt
        self.speed = min(S.MAX_FALL_SPEED,
                         S.BASE_FALL_SPEED + self.run_time * S.SPEED_BY_TIME
                         + self.score * S.SPEED_BY_SCORE)

        # move the falling object
        self.obj.update(dt, self.speed, self.width, self.height)
        self.basket.set_y(self.basket_y)
        catch = self.basket.catch_rect()

        if self.obj.rect().colliderect(catch):
            self._on_catch(self.obj.kind)
        elif self.obj.off_screen(self.height):
            self._on_miss(self.obj.kind)

    def _on_catch(self, kind):
        if kind == APPLE:
            self.score += 1
            self.audio.play("pop")
            self._spawn()
        elif kind == BOMB:
            if self.timers["shield"] > 0:
                self.audio.play("chime")   # shield absorbs it
                self._spawn()
            else:
                self.blast = Blast(int(self.obj.x), int(self.obj.y))
                self.dying = True
                self.audio.play("boom")
        elif kind == SHIELD:
            self.timers["shield"] = S.SHIELD_TIME
            self.audio.play("chime")
            self._spawn()
        elif kind == EXTEND:
            self.timers["extend"] = S.EXTEND_TIME
            self.basket.set_extended(True, self.width)
            self.audio.play("chime")
            self._spawn()
        elif kind == HEART:
            if self.lives < S.START_LIVES:
                self.lives += 1          # restore a lost heart
            else:
                self.score += 2          # already full -> small bonus instead
            self.audio.play("chime")
            self._spawn()

    def _on_miss(self, kind):
        if kind == APPLE:
            self.lives -= 1
            if self.lives <= 0:
                self.finalize_game_over("hearts")
                return
        self._spawn()

    def _spawn(self):
        self.obj = FallingObject(self.width, self.height)

    # --- render -------------------------------------------------------------
    def _layout(self):
        cx = self.width // 2
        h = self.height
        self.btn_play.place((cx, int(h * 0.55)), (300, 64))
        self.btn_help.place((cx, int(h * 0.645)), (300, 58))
        self.btn_quit.place((cx, int(h * 0.735)), (300, 56))

        panel_top = h // 2 - 250
        self.btn_ad.place((cx, panel_top + 360), (420, 58))
        self.btn_again.place((cx, panel_top + 430), (300, 56))
        self.btn_menu.place((cx, panel_top + 495), (300, 52))

        # Help-screen back button sits at the bottom of the help panel
        panel_h = min(600, int(h * 0.84))
        self.btn_back.place((cx, h // 2 + panel_h // 2 - 48), (240, 52))
        self.btn_ad.text = "CONTINUE  (free!)" if self.ad_unlocked else "WATCH AD TO CONTINUE"
        self.btn_ad.base = (60, 150, 70) if self.ad_unlocked else (200, 120, 40)
        self.btn_ad.hover = (80, 185, 90) if self.ad_unlocked else (230, 150, 60)

    def render(self):
        mouse = pygame.mouse.get_pos()
        self._layout()
        self.screen.blit(self.assets.background((self.width, self.height)), (0, 0))

        if self.scene == MENU:
            self._draw_menu(mouse)
        elif self.scene == HELP:
            self._draw_help(mouse)
        elif self.scene == PLAYING:
            self._draw_play(mouse)
        else:
            self._draw_over(mouse)

        ui.draw_window_buttons(self.screen, self.width, self.is_fullscreen, mouse)
        pygame.display.flip()

    def _draw_logo(self, cx, cy, max_w_frac, max_h_frac):
        logo = self.assets.img("logo")
        max_w, max_h = self.width * max_w_frac, self.height * max_h_frac
        scale = min(max_w / logo.get_width(), max_h / logo.get_height())
        lw, lh = int(logo.get_width() * scale), int(logo.get_height() * scale)
        logo_s = self.assets.scaled("logo", (lw, lh))
        self.screen.blit(logo_s, logo_s.get_rect(center=(cx, cy)))

    def _draw_menu(self, mouse):
        for d in self._menu_decor:
            img = self.assets.scaled(d["kind"], (d["size"], d["size"]))
            self.screen.blit(img, (int(d["x"]), int(d["y"])))

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        self.screen.blit(overlay, (0, 0))

        cx = self.width // 2
        self._draw_logo(cx, int(self.height * 0.23), 0.62, 0.36)

        # compact high-score chip
        hs = pygame.Rect(0, 0, 250, 64)
        hs.center = (cx, int(self.height * 0.455))
        s = pygame.Surface(hs.size, pygame.SRCALPHA)
        s.fill((0, 0, 0, 130))
        self.screen.blit(s, hs.topleft)
        pygame.draw.rect(self.screen, S.GOLD, hs, width=3, border_radius=14)
        ui.text_center(self.screen, "HIGH SCORE", self.assets.font_tiny, cx, hs.top + 18,
                       S.GOLD, shadow=False)
        ui.text_center(self.screen, str(self.high_score), self.assets.font_mid, cx,
                       hs.top + 44, S.WHITE)

        self.btn_play.draw(self.screen, mouse)
        self.btn_help.draw(self.screen, mouse)
        self.btn_quit.draw(self.screen, mouse)

    HELP_LINES = [
        ("apple", "Catch falling apples - each one is worth 1 point."),
        ("bomb", "Never catch a bomb - it explodes and ends the game!"),
        ("heart_full", "You start with 3 hearts. Miss an apple, lose a heart."),
        ("apple", "Watch out: apples morph into bombs mid-fall..."),
        ("bomb", "...and bombs morph into apples. Don't be fooled!"),
        ("shield", "Shield (rare): blocks bombs for 15 seconds."),
        ("extend", "Extend (rare): widens your basket for 9 seconds."),
        ("heart_full", "Heart (rare): restores a lost heart."),
        (None, "Move with  <-  ->  or  A / D."),
        (None, "Double-tap a direction to DASH (3s speed boost)."),
        (None, "Game over? Watch a short ad to continue & keep your score."),
    ]

    def _draw_help(self, mouse):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        cx = self.width // 2
        pw = min(680, int(self.width * 0.9))
        ph = min(600, int(self.height * 0.84))
        panel = pygame.Rect(0, 0, pw, ph)
        panel.center = (cx, self.height // 2)
        pygame.draw.rect(self.screen, S.PANEL_BG, panel, border_radius=24)
        pygame.draw.rect(self.screen, S.GOLD, panel, width=3, border_radius=24)

        ui.text_center(self.screen, "HOW TO PLAY", self.assets.font_big, cx,
                       panel.top + 48, S.GOLD)

        x = panel.left + 34
        y = panel.top + 104
        step = (panel.bottom - 80 - y) / len(self.HELP_LINES)
        for icon, text in self.HELP_LINES:
            if icon:
                self.screen.blit(self.assets.scaled(icon, (30, 30)), (x, int(y) - 4))
            label = self.assets.font_tiny.render(text, True, S.WHITE)
            self.screen.blit(label, (x + 42, int(y)))
            y += step

        self.btn_back.draw(self.screen, mouse)

    def _draw_play(self, mouse):
        if not self.dying:
            self.obj.draw(self.screen, self.assets)
        self.basket.draw(self.screen, self.assets, self.basket_y,
                         shield_on=self.timers["shield"] > 0)
        if self.blast:
            self.blast.draw(self.screen)

        # HUD: hearts + score (left), best (left), timers (centre)
        ui.draw_hearts(self.screen, self.assets, self.lives, S.START_LIVES, (18, 18))
        score = self.assets.font_mid.render(f"{self.score}", True, S.WHITE)
        sh = self.assets.font_mid.render(f"{self.score}", True, S.BLACK)
        apple_ic = self.assets.scaled("apple", (34, 34))
        self.screen.blit(apple_ic, (20, 66))
        self.screen.blit(sh, (62, 62)); self.screen.blit(score, (60, 60))
        best = self.assets.font_tiny.render(f"Best: {self.high_score}", True, S.GOLD)
        self.screen.blit(best, (20, 108))

        ui.draw_powerup_bar(self.screen, self.assets, self.timers, self.width)

    def _draw_over(self, mouse):
        # frozen scene behind the panel
        self.basket.draw(self.screen, self.assets, self.basket_y)
        if self.blast and not self.blast.done:
            self.blast.draw(self.screen)

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        cx = self.width // 2
        panel = pygame.Rect(0, 0, 500, 540)
        panel.center = (cx, self.height // 2)
        pygame.draw.rect(self.screen, S.PANEL_BG, panel, border_radius=26)
        pygame.draw.rect(self.screen, S.PANEL_EDGE, panel, width=3, border_radius=26)
        top = panel.top

        headline = "BOOM!" if self.over_reason == "bomb" else "GAME OVER"
        ui.text_center(self.screen, headline, self.assets.font_big, cx, top + 56, S.ACCENT)
        sub = "You caught a bomb" if self.over_reason == "bomb" else "Out of hearts"
        ui.text_center(self.screen, sub, self.assets.font_small, cx, top + 104,
                       (220, 220, 220), shadow=False)

        if self.new_high:
            badge = pygame.Rect(0, 0, 290, 38); badge.center = (cx, top + 146)
            pygame.draw.rect(self.screen, S.GOLD, badge, border_radius=19)
            ui.text_center(self.screen, "NEW HIGH SCORE!", self.assets.font_tiny, cx,
                           badge.centery, (60, 45, 0), shadow=False)

        ui.text_center(self.screen, "Apples caught", self.assets.font_small, cx, top + 192,
                       (210, 210, 210), shadow=False)
        ui.text_center(self.screen, str(self.score), self.assets.font_title, cx, top + 238, S.WHITE)
        ui.text_center(self.screen, f"Best: {self.high_score}", self.assets.font_small, cx,
                       top + 290, S.GOLD, shadow=False)

        # ad status line
        if self.ad_active and not self.ad_unlocked:
            left = max(0, S.AD_UNLOCK_TIME - self.ad_elapsed)
            ui.text_center(self.screen,
                           f"Watching ad in your browser... continue in {left:0.0f}s",
                           self.assets.font_tiny, cx, panel.top + 332, S.BOOST_CLR, shadow=False)
        elif self.ad_unlocked:
            ui.text_center(self.screen, "Ad complete - tap Continue to keep your score!",
                           self.assets.font_tiny, cx, panel.top + 332, S.GREEN_HI, shadow=False)

        self.btn_ad.draw(self.screen, mouse)
        self.btn_again.draw(self.screen, mouse)
        self.btn_menu.draw(self.screen, mouse)

    # --- main loop ----------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(S.FPS) / 1000.0
            running = self.handle_events()
            if running:
                self.update(dt)
                self.render()
        pygame.quit()
