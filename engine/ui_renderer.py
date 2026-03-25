import pygame
import OpenGL.GL as gl
import OpenGL.GL.shaders
import numpy as np
import ctypes
import os

class UIRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.font.init()
        self.title_font = pygame.font.SysFont("Impact", 72)
        self.font = pygame.font.SysFont("Impact", 42)

        # Load GameOver Image
        self.gameover_img = None
        if os.path.exists("assets/gameover.png"):
            try:
                img = pygame.image.load("assets/gameover.png").convert_alpha()
                target_width = int(self.width * 0.6)
                target_height = int(target_width * (img.get_height() / img.get_width()))
                self.gameover_img = pygame.transform.smoothscale(img, (target_width, target_height))
            except: pass

        # Load Logo Image
        self.logo_img = None
        if os.path.exists("assets/logo.png"):
            try:
                img = pygame.image.load("assets/logo.png").convert_alpha()
                target_h = 200
                target_w = int(target_h * (img.get_width() / img.get_height()))
                self.logo_img = pygame.transform.smoothscale(img, (target_w, target_h))
            except: pass
            
        # Load Background Banner (For Main Menu)
        self.banner_img = None
        if os.path.exists("assets/banner.png"):
            try:
                img = pygame.image.load("assets/banner.png").convert_alpha()
                self.banner_img = pygame.transform.smoothscale(img, (self.width, self.height))
            except: pass

        # --- Load your Pre-Blurred Level Background ---
        self.level_bg = None
        if os.path.exists("assets/level.png"):
            try:
                img = pygame.image.load("assets/level.png").convert_alpha()
                self.level_bg = pygame.transform.smoothscale(img, (self.width, self.height))
            except: pass

        # Load Difficulty Thumbnails (16:9 Aspect Ratio)
        self.diff_thumbs = {}
        for diff_name, file_name in [("EASY", "easy.png"), ("NORMAL", "medium.png"), ("HARD", "hard.png")]:
            path = f"assets/{file_name}"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Scale to a 16:9 small card size (e.g., 256x144)
                    self.diff_thumbs[diff_name] = pygame.transform.smoothscale(img, (256, 144))
                except: pass

        self.tex_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_id)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        self._compile_shaders()
        self._setup_quad()

    def _compile_shaders(self):
        with open("shaders/ui_vertex.glsl", "r") as f: v_src = f.read()
        with open("shaders/ui_fragment.glsl", "r") as f: f_src = f.read()
        self.shader = gl.shaders.compileProgram(
            gl.shaders.compileShader(v_src, gl.GL_VERTEX_SHADER),
            gl.shaders.compileShader(f_src, gl.GL_FRAGMENT_SHADER)
        )

    def _setup_quad(self):
        vertices = np.array([-1,-1,0,0, 1,-1,1,0, 1,1,1,1, 1,1,1,1, -1,1,0,1, -1,-1,0,0], dtype=np.float32)
        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)
        self.vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)

    def draw_text_centered(self, text, font, color, y_offset=0):
        surface = font.render(text, True, color)
        shadow = font.render(text, True, (0, 0, 0))
        rect = surface.get_rect(center=(self.width // 2, self.height // 2 + y_offset))
        self.surface.blit(shadow, (rect.x + 3, rect.y + 3))
        self.surface.blit(surface, rect)

    def draw(self, state_str, health, score, highscore_data=None, current_diff="NORMAL", fade_alpha=0.0):
        self.surface.fill((0, 0, 0, 0))
        mx, my = pygame.mouse.get_pos()
        cx, cy = self.width // 2, self.height // 2

        if state_str == "SPLASH_SCREEN":
            self.surface.fill((0, 0, 0, 255)) 
            title_surf = self.title_font.render("3D RPG SHOOTER", True, (255, 255, 255))
            if self.logo_img:
                gap = 40
                total_w = self.logo_img.get_width() + gap + title_surf.get_width()
                start_x = cx - total_w // 2
                self.surface.blit(self.logo_img, (start_x, cy - self.logo_img.get_height() // 2))
                self.surface.blit(title_surf, (start_x + self.logo_img.get_width() + gap, cy - title_surf.get_height() // 2))
            else:
                self.surface.blit(title_surf, title_surf.get_rect(center=(cx, cy)))

        elif state_str == "MAIN_MENU":
            if self.banner_img:
                self.surface.blit(self.banner_img, (0, 0))
            else:
                self.surface.fill((20, 25, 35, 255))
                self.draw_text_centered("3D RPG SHOOTER", self.title_font, (0, 255, 100), -150)

            buttons = [("START GAME", 50), ("QUIT", 130)]
            for text, y_off in buttons:
                rect = pygame.Rect(0, 0, 300, 60); rect.center = (cx, cy + y_off)
                if rect.collidepoint((mx, my)):
                    pygame.draw.rect(self.surface, (100, 100, 100), rect)
                    pygame.draw.rect(self.surface, (0, 255, 100), rect, 3) 
                    self.draw_text_centered(text, self.font, (0, 255, 100), y_off)
                else:
                    pygame.draw.rect(self.surface, (50, 50, 50), rect)
                    pygame.draw.rect(self.surface, (255, 255, 255), rect, 3) 
                    self.draw_text_centered(text, self.font, (255, 255, 255), y_off)
            pygame.draw.circle(self.surface, (255, 255, 255), (mx, my), 8, 2)

        elif state_str == "DIFFICULTY_MENU":
            # --- Draw the level.png background ---
            if self.level_bg: 
                self.surface.blit(self.level_bg, (0, 0))
            elif self.banner_img:
                self.surface.blit(self.banner_img, (0, 0))
                self.surface.fill((0, 0, 0, 180)) 
            else: 
                self.surface.fill((0, 0, 0, 200)) 

            self.draw_text_centered("SELECT DIFFICULTY", self.title_font, (255, 255, 255), -220)

            # Draw Thumbnail Cards
            diffs = [("EASY", -300), ("NORMAL", 0), ("HARD", 300)]
            for diff_text, x_off in diffs:
                rect = pygame.Rect(0, 0, 256, 144)
                rect.center = (cx + x_off, cy - 10)
                
                is_hover = rect.collidepoint((mx, my))
                is_selected = (current_diff == diff_text)
                border_color = (0, 255, 100) if is_selected else (200, 200, 200)

                # Draw the Image if it exists, otherwise a fallback box
                if diff_text in self.diff_thumbs:
                    self.surface.blit(self.diff_thumbs[diff_text], rect.topleft)
                else:
                    pygame.draw.rect(self.surface, (80, 80, 80), rect)
                    self.draw_text_centered(diff_text, self.font, (255, 255, 255), -10)
                
                # Draw selection/hover border
                if is_hover or is_selected:
                    pygame.draw.rect(self.surface, border_color, rect, 4)

            # Draw Start and Back buttons
            actions = [("START", 130), ("BACK", 210)]
            for text, y_off in actions:
                rect = pygame.Rect(0, 0, 300, 60); rect.center = (cx, cy + y_off)
                color = (0, 255, 100) if text == "START" else (255, 255, 255)
                if rect.collidepoint((mx, my)):
                    pygame.draw.rect(self.surface, (100, 100, 100), rect)
                    pygame.draw.rect(self.surface, color, rect, 3)
                    text_surf = self.font.render(text, True, color)
                else:
                    pygame.draw.rect(self.surface, (50, 50, 50), rect)
                    pygame.draw.rect(self.surface, (200, 200, 200), rect, 3)
                    text_surf = self.font.render(text, True, (200, 200, 200))
                self.surface.blit(text_surf, text_surf.get_rect(center=rect.center))
            pygame.draw.circle(self.surface, (255, 255, 255), (mx, my), 8, 2)

        elif state_str == "GAMEPLAY":
            pygame.draw.rect(self.surface, (50, 50, 50), (20, 20, 200, 25))
            pygame.draw.rect(self.surface, (50, 255, 50) if health > 30 else (255, 50, 50), (20, 20, max(0, health) * 2, 25))
            pygame.draw.rect(self.surface, (255, 255, 255), (20, 20, 200, 25), 3)
            score_txt = self.font.render(f"SCORE: {score}", True, (255, 200, 50))
            self.surface.blit(score_txt, (20, 60))
            pygame.draw.circle(self.surface, (0, 255, 100), (mx, my), 18, 2)
            pygame.draw.circle(self.surface, (255, 50, 50), (mx, my), 3)

        elif state_str == "PAUSED":
            self.surface.fill((0, 0, 0, 180)) 
            self.draw_text_centered("GAME PAUSED", self.title_font, (255, 255, 255), -150)
            buttons = [("RESUME", -40), ("RESTART", 40), ("MAIN MENU", 120)]
            for text, y_off in buttons:
                rect = pygame.Rect(0, 0, 300, 60); rect.center = (cx, cy + y_off)
                if rect.collidepoint((mx, my)):
                    pygame.draw.rect(self.surface, (100, 100, 100), rect)
                    pygame.draw.rect(self.surface, (0, 255, 100), rect, 3) 
                    self.draw_text_centered(text, self.font, (0, 255, 100), y_off)
                else:
                    pygame.draw.rect(self.surface, (50, 50, 50), rect)
                    pygame.draw.rect(self.surface, (255, 255, 255), rect, 3) 
                    self.draw_text_centered(text, self.font, (255, 255, 255), y_off)
            pygame.draw.circle(self.surface, (255, 255, 255), (mx, my), 8, 2)

        elif state_str == "GAME_OVER":
            self.surface.fill((50, 0, 0, 180)) 
            if self.gameover_img:
                b_rect = self.gameover_img.get_rect(center=(cx, cy - 120))
                self.surface.blit(self.gameover_img, b_rect)
            else:
                self.draw_text_centered("MISSION FAILED", self.title_font, (255, 50, 50), -120)
                
            self.draw_text_centered(f"FINAL SCORE: {score}", self.font, (255, 200, 50), 10)
            
            # --- NEW: Interactive Game Over Buttons ---
            buttons = [("RESTART", 100), ("MAIN MENU", 180)]
            for text, y_off in buttons:
                rect = pygame.Rect(0, 0, 300, 60); rect.center = (cx, cy + y_off)
                if rect.collidepoint((mx, my)):
                    pygame.draw.rect(self.surface, (100, 100, 100), rect)
                    pygame.draw.rect(self.surface, (0, 255, 100), rect, 3) 
                    self.draw_text_centered(text, self.font, (0, 255, 100), y_off)
                else:
                    pygame.draw.rect(self.surface, (50, 50, 50), rect)
                    pygame.draw.rect(self.surface, (255, 255, 255), rect, 3) 
                    self.draw_text_centered(text, self.font, (255, 255, 255), y_off)
            pygame.draw.circle(self.surface, (255, 255, 255), (mx, my), 8, 2)

        # --- GLOBAL SCREEN FADE OVERLAY ---
        if fade_alpha > 0.0:
            fade_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(min(255, max(0, fade_alpha)))))
            self.surface.blit(fade_surf, (0, 0))

        data = pygame.image.tobytes(self.surface, "RGBA", True)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        
        gl.glUseProgram(self.shader)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_DEPTH_TEST) 
        gl.glBindVertexArray(self.vao)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_id)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
        gl.glEnable(gl.GL_DEPTH_TEST)