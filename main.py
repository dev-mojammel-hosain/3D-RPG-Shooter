import os
import ctypes
import json 

# Force Windows to respect Pygame's DPI so it doesn't crop the screen
try:
    ctypes.windll.user32.SetProcessDPIAware()
except AttributeError:
    pass

import pygame
from pygame.locals import *
import OpenGL.GL as gl
import glm
import random
import math

from systems.state_machine import StateMachine, GameState
from engine.camera import Camera
from engine.renderer import Renderer
from engine.mesh import Mesh
from engine.ui_renderer import UIRenderer

from entities.player import Player
from entities.projectile import Projectile
from entities.enemy import Enemy
from entities.box import Box

# --- JSON Highscore Logic ---
def load_highscore():
    if os.path.exists("highscore.json"):
        try:
            with open("highscore.json", "r") as f:
                return json.load(f)
        except: pass
    return {"score": 0, "level": "NORMAL"}

def save_highscore(score, level):
    data = load_highscore()
    if score > data["score"]:
        with open("highscore.json", "w") as f:
            json.dump({"score": score, "level": level}, f)

def check_aabb_collision(x1, z1, w1, d1, x2, z2, w2, d2):
    return abs(x1 - x2) < (w1 + w2) / 2.0 and abs(z1 - z2) < (d1 + d2) / 2.0

def main():
    pygame.init()
    
    # --- Force Windows to use Modern OpenGL (3.3 Core) ---
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

    # --- SETUP RESOLUTION ---
    display_resolution = (1920, 1080)
    pygame.display.set_mode(display_resolution, DOUBLEBUF | OPENGL | FULLSCREEN)
    pygame.display.set_caption("3D RPG Shooter - OpenGL Engine")

    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    state_machine = StateMachine()

    camera = Camera(display_resolution[0], display_resolution[1])
    
    # Fix Far Clipping Plane
    aspect = display_resolution[0] / display_resolution[1]
    camera.projection_matrix = glm.ortho(
        -camera.zoom * aspect, camera.zoom * aspect, 
        -camera.zoom, camera.zoom, 
        -500.0, 500.0 
    )

    renderer = Renderer()
    ui_renderer = UIRenderer(display_resolution[0], display_resolution[1])
    
    print("Loading 3D Models & Textures...")
    player_mesh = Mesh("assets/models/player.glb")
    enemy_mesh = Mesh("assets/models/enemy.glb")
    bullet_mesh = Mesh("assets/models/bullet-foam-tip.glb")
    crate_mesh = Mesh("assets/models/crate-medium.glb")
    player_gun_mesh = Mesh("assets/models/player_gun.glb")
    enemy_gun_mesh = Mesh("assets/models/enemy_gun.glb")
    
    car_tex = renderer.load_texture("assets/models/car_map.png")
    blaster_tex = renderer.load_texture("assets/models/blaster_map.png")
    
    ARENA_SIZE = 140.0 
    player = Player(0.0, 0.0)
    player_health = 100.0
    score = 0
    
    active_bullets = []
    active_enemy_bullets = []
    active_enemies = []
    max_enemies = 5 
    
    active_boxes = []
    max_boxes = 80
    for _ in range(max_boxes):
        active_boxes.append(Box(random.uniform(-ARENA_SIZE, ARENA_SIZE), random.uniform(-ARENA_SIZE, ARENA_SIZE)))

    wall_matrices = [
        glm.scale(glm.rotate(glm.translate(glm.mat4(1.0), glm.vec3(0, 5, -ARENA_SIZE)), math.pi/2, glm.vec3(1, 0, 0)), glm.vec3(ARENA_SIZE*2, 1.0, 10.0)),
        glm.scale(glm.rotate(glm.translate(glm.mat4(1.0), glm.vec3(0, 5, ARENA_SIZE)), -math.pi/2, glm.vec3(1, 0, 0)), glm.vec3(ARENA_SIZE*2, 1.0, 10.0)), 
        glm.scale(glm.rotate(glm.translate(glm.mat4(1.0), glm.vec3(ARENA_SIZE, 5, 0)), math.pi/2, glm.vec3(0, 0, 1)), glm.vec3(10.0, 1.0, ARENA_SIZE*2)), 
        glm.scale(glm.rotate(glm.translate(glm.mat4(1.0), glm.vec3(-ARENA_SIZE, 5, 0)), -math.pi/2, glm.vec3(0, 0, 1)), glm.vec3(10.0, 1.0, ARENA_SIZE*2))  
    ]

    # --- Screen Transition Variables ---
    state_machine.current_state = "SPLASH_SCREEN"
    splash_timer = 0.0
    current_difficulty = "NORMAL"
    highscore_data = load_highscore()
    
    fade_alpha = 255.0 # Start fully black so it fades in beautifully
    transitioning = False
    target_state = None
    pending_action = None

    def start_transition(new_state, action=None):
        nonlocal transitioning, target_state, pending_action
        if not transitioning:
            transitioning = True
            target_state = new_state
            pending_action = action

    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0 
        state_name = state_machine.current_state.name if hasattr(state_machine.current_state, 'name') else str(state_machine.current_state)

        # --- Transition Engine ---
        if transitioning:
            fade_alpha += 800.0 * delta_time # Fade to black
            if fade_alpha >= 255.0:
                fade_alpha = 255.0
                state_machine.current_state = target_state
                transitioning = False
                
                # Execute resets while hidden in the dark!
                if pending_action == "RESET_GAME":
                    player.x, player.z = 0.0, 0.0; player_health = 100.0; score = 0
                    active_bullets.clear(); active_enemy_bullets.clear(); active_enemies.clear(); active_boxes.clear()
                    for _ in range(max_boxes): active_boxes.append(Box(random.uniform(-ARENA_SIZE, ARENA_SIZE), random.uniform(-ARENA_SIZE, ARENA_SIZE)))
                    
                    if current_difficulty == "EASY": max_enemies = 3
                    elif current_difficulty == "NORMAL": max_enemies = 5
                    elif current_difficulty == "HARD": max_enemies = 8
                
                pending_action = None
        else:
            fade_alpha -= 800.0 * delta_time # Fade to clear
            if fade_alpha < 0.0: fade_alpha = 0.0

        if state_name == "SPLASH_SCREEN" and not transitioning:
            splash_timer += delta_time
            if splash_timer >= 3.0: 
                start_transition("MAIN_MENU")

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
                
            # --- MOUSE CLICK LOGIC ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not transitioning: 
                mx, my = pygame.mouse.get_pos()
                cx, cy = display_resolution[0] // 2, display_resolution[1] // 2
                
                if state_name == "MAIN_MENU":
                    rect_start = pygame.Rect(0, 0, 300, 60); rect_start.center = (cx, cy + 50)
                    rect_quit = pygame.Rect(0, 0, 300, 60);  rect_quit.center = (cx, cy + 130)
                    if rect_start.collidepoint((mx, my)):
                        highscore_data = load_highscore() 
                        start_transition("DIFFICULTY_MENU")
                    elif rect_quit.collidepoint((mx, my)):
                        running = False
                        
                elif state_name == "DIFFICULTY_MENU":
                    # Hitboxes match the 256x144 thumbnail cards
                    rect_easy = pygame.Rect(0, 0, 256, 144); rect_easy.center = (cx - 300, cy - 10)
                    rect_normal = pygame.Rect(0, 0, 256, 144); rect_normal.center = (cx, cy - 10)
                    rect_hard = pygame.Rect(0, 0, 256, 144); rect_hard.center = (cx + 300, cy - 10)
                    
                    rect_start = pygame.Rect(0, 0, 300, 60); rect_start.center = (cx, cy + 130)
                    rect_back = pygame.Rect(0, 0, 300, 60); rect_back.center = (cx, cy + 210)

                    if rect_easy.collidepoint((mx, my)): current_difficulty = "EASY"
                    elif rect_normal.collidepoint((mx, my)): current_difficulty = "NORMAL"
                    elif rect_hard.collidepoint((mx, my)): current_difficulty = "HARD"
                    elif rect_back.collidepoint((mx, my)): start_transition("MAIN_MENU")
                    elif rect_start.collidepoint((mx, my)): start_transition("GAMEPLAY", "RESET_GAME")

                elif state_name == "PAUSED":
                    rect_resume = pygame.Rect(0, 0, 300, 60);  rect_resume.center = (cx, cy - 40)
                    rect_restart = pygame.Rect(0, 0, 300, 60); rect_restart.center = (cx, cy + 40)
                    rect_menu = pygame.Rect(0, 0, 300, 60);    rect_menu.center = (cx, cy + 120)
                    
                    if rect_resume.collidepoint((mx, my)): start_transition("GAMEPLAY")
                    elif rect_restart.collidepoint((mx, my)): start_transition("GAMEPLAY", "RESET_GAME")
                    elif rect_menu.collidepoint((mx, my)): start_transition("MAIN_MENU")

                elif state_name == "GAME_OVER":
                    # Updated Game Over Buttons
                    rect_restart = pygame.Rect(0, 0, 300, 60); rect_restart.center = (cx, cy + 100)
                    rect_menu = pygame.Rect(0, 0, 300, 60); rect_menu.center = (cx, cy + 180)
                    
                    if rect_restart.collidepoint((mx, my)): start_transition("GAMEPLAY", "RESET_GAME")
                    elif rect_menu.collidepoint((mx, my)): start_transition("MAIN_MENU")

            # --- KEYBOARD LOGIC ---
            if event.type == pygame.KEYDOWN and not transitioning:
                if state_name == "GAMEPLAY" and event.key == pygame.K_ESCAPE: start_transition("PAUSED")
                elif state_name == "PAUSED" and event.key == pygame.K_ESCAPE: start_transition("GAMEPLAY")

        gl.glViewport(0, 0, display_resolution[0], display_resolution[1])
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        if state_name == "GAMEPLAY" and not transitioning:
            player.update(delta_time, camera)
            player.x = max(-ARENA_SIZE, min(ARENA_SIZE, player.x)); player.z = max(-ARENA_SIZE, min(ARENA_SIZE, player.z))
            
            if hasattr(camera, 'follow_target'): camera.follow_target(player.x, player.z, delta_time)
            
            # --- 100% ACCURATE RAYCAST AIMING ---
            mx, my = pygame.mouse.get_pos()
            view = camera.get_view_matrix(); proj = camera.get_projection_matrix()
            viewport = glm.vec4(0, 0, display_resolution[0], display_resolution[1])
            world_near = glm.unProject(glm.vec3(mx, display_resolution[1]-my, 0), view, proj, viewport)
            world_far = glm.unProject(glm.vec3(mx, display_resolution[1]-my, 1), view, proj, viewport)
            ray_dir = glm.normalize(world_far - world_near)
            if ray_dir.y != 0:
                t = (1.0 - world_near.y) / ray_dir.y
                hit = world_near + ray_dir * t
                player.rotation_y = math.atan2(hit.x - player.x, hit.z - player.z)
            
            if player.can_shoot(): active_bullets.append(Projectile(player.x, player.z, player.rotation_y))
                
            while len(active_enemies) < max_enemies:
                spawn_x = player.x + random.choice([-25, 25]); spawn_z = player.z + random.uniform(-25, 25)
                active_enemies.append(Enemy(max(-ARENA_SIZE, min(ARENA_SIZE, spawn_x)), max(-ARENA_SIZE, min(ARENA_SIZE, spawn_z))))
            
            for enemy in active_enemies:
                enemy.update(delta_time, player.x, player.z)
                if check_aabb_collision(player.x, player.z, 2.0, 2.0, enemy.x, enemy.z, enemy.width, enemy.depth):
                    player_health -= 15 * delta_time 
                if hasattr(enemy, 'can_shoot') and enemy.can_shoot():
                    angle = math.atan2(player.x - enemy.x, player.z - enemy.z)
                    active_enemy_bullets.append(Projectile(enemy.x, enemy.z, angle, 15.0))
            
            for i in range(len(active_bullets)-1, -1, -1):
                b = active_bullets[i]; b.update(delta_time); hit = False
                for e in active_enemies:
                    if check_aabb_collision(b.x, b.z, 2.0, 2.0, e.x, e.z, e.width, e.depth):
                        e.health -= 1; hit = True; e.color = (5, 0, 0)
                        if e.health <= 0: active_enemies.remove(e); score += 50
                        break
                if not hit:
                    for box in active_boxes:
                        if check_aabb_collision(b.x, b.z, 2.0, 2.0, box.x, box.z, box.width, box.depth):
                            box.health -= 1; hit = True; box.color = (5, 0, 0)
                            if box.health <= 0: active_boxes.remove(box); score += 10
                            break
                if hit or b.age >= b.lifespan: active_bullets.pop(i)

            for i in range(len(active_enemy_bullets)-1, -1, -1):
                eb = active_enemy_bullets[i]; eb.update(delta_time)
                if check_aabb_collision(eb.x, eb.z, 2.0, 2.0, player.x, player.z, player.width, player.depth):
                    player_health -= 10; active_enemy_bullets.pop(i)
                elif eb.age >= eb.lifespan: active_enemy_bullets.pop(i)

            if player_health <= 0:
                save_highscore(score, current_difficulty)
                highscore_data = load_highscore()
                start_transition("GAME_OVER")

        # --- 3D RENDER PASS ---
        if state_name not in ["SPLASH_SCREEN", "MAIN_MENU", "DIFFICULTY_MENU"]:
            floor_mat = glm.scale(glm.translate(glm.mat4(1.0), glm.vec3(0, -0.1, 0)), glm.vec3(300, 0.1, 300))
            renderer.render(camera, floor_mat, is_floor=True)

            gl.glDepthMask(gl.GL_FALSE)
            for box in active_boxes: renderer.render(camera, box.get_model_matrix(), custom_mesh=crate_mesh, is_shadow=True)
            for e in active_enemies:
                e_mat = glm.rotate(glm.translate(glm.mat4(1.0), glm.vec3(e.x, 0, e.z)), math.atan2(player.x - e.x, player.z - e.z), glm.vec3(0, 1, 0))
                renderer.render(camera, e_mat, custom_mesh=enemy_mesh, is_shadow=True)
            p_mat = glm.rotate(glm.translate(glm.mat4(1.0), glm.vec3(player.x, 0, player.z)), player.rotation_y, glm.vec3(0, 1, 0))
            renderer.render(camera, p_mat, custom_mesh=player_mesh, is_shadow=True)
            gl.glDepthMask(gl.GL_TRUE)

            for box in active_boxes:
                renderer.render(camera, box.get_model_matrix(), color=box.color, custom_mesh=crate_mesh, texture_id=blaster_tex)
                box.color = (1,1,1)
            for e in active_enemies:
                e_mat = glm.rotate(glm.translate(glm.mat4(1.0), glm.vec3(e.x, 0, e.z)), math.atan2(player.x - e.x, player.z - e.z), glm.vec3(0, 1, 0))
                renderer.render(camera, e_mat, color=e.color, custom_mesh=enemy_mesh, texture_id=car_tex); e.color = (1,1,1)
                g_mat = glm.scale(glm.rotate(glm.translate(e_mat, glm.vec3(0, 2.2, 0)), math.pi, glm.vec3(0, 1, 0)), glm.vec3(3.0))
                renderer.render(camera, g_mat, custom_mesh=enemy_gun_mesh, texture_id=blaster_tex)

            for w_mat in wall_matrices: renderer.render(camera, w_mat, color=(0.2, 0.2, 0.25), custom_mesh=None)
            renderer.render(camera, p_mat, custom_mesh=player_mesh, texture_id=car_tex)
            pg_mat = glm.scale(glm.rotate(glm.translate(p_mat, glm.vec3(0, 1.2, 0)), math.pi, glm.vec3(0, 1, 0)), glm.vec3(3.0))
            renderer.render(camera, pg_mat, custom_mesh=player_gun_mesh, texture_id=blaster_tex)

            for b in active_bullets: renderer.render(camera, b.get_model_matrix(), custom_mesh=bullet_mesh, texture_id=blaster_tex)
            for eb in active_enemy_bullets: renderer.render(camera, eb.get_model_matrix(), color=(1, 0.5, 0), custom_mesh=bullet_mesh, texture_id=blaster_tex)

        # --- UI RENDER PASS ---
        ui_renderer.draw(state_name, player_health, score, highscore_data, current_difficulty, fade_alpha)
        
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()