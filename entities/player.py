import pygame
import glm
import math

class Player:
    def __init__(self, start_x=0.0, start_z=0.0):
        self.x = start_x
        self.z = start_z
        self.width = 2.0
        self.depth = 2.0
        self.speed = 8.0 
        self.rotation_y = 0.0 
        
        self.fire_rate = 0.4  
        self.fire_timer = 0.0  

    def update(self, delta_time, camera):
        # 1. Keyboard Movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: self.z -= self.speed * delta_time
        if keys[pygame.K_s]: self.z += self.speed * delta_time
        if keys[pygame.K_a]: self.x -= self.speed * delta_time
        if keys[pygame.K_d]: self.x += self.speed * delta_time

        self.fire_timer += delta_time

        # --- 2. TRUE PINPOINT AIMING (Screen-to-World Raycast) ---
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # OpenGL coordinates start at the bottom, Pygame starts at the top. Flip Y!
        gl_mouse_y = 720 - mouse_y 

        view = camera.get_view_matrix()
        proj = camera.get_projection_matrix()
        
        # This must match your Pygame window resolution
        viewport = glm.vec4(0, 0, 1280, 720)

        # Unproject the 2D mouse position into 3D space (Near plane and Far plane)
        near_pt = glm.unProject(glm.vec3(mouse_x, gl_mouse_y, 0.0), view, proj, viewport)
        far_pt  = glm.unProject(glm.vec3(mouse_x, gl_mouse_y, 1.0), view, proj, viewport)

        # Calculate the direction the mouse ray is pointing in the 3D world
        ray_dir = glm.normalize(far_pt - near_pt)

        # Find where that ray intersects the horizontal plane at the gun's height (Y = 1.0)
        if ray_dir.y != 0:
            t = (1.0 - near_pt.y) / ray_dir.y
            target_x = near_pt.x + ray_dir.x * t
            target_z = near_pt.z + ray_dir.z * t
            
            # Rotate the player to face this exact 3D coordinate!
            dx = target_x - self.x
            dz = target_z - self.z
            self.rotation_y = math.atan2(dx, dz)

    def can_shoot(self):
        if self.fire_timer >= self.fire_rate:
            self.fire_timer = 0.0 
            return True
        return False

    def get_model_matrix(self):
        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(self.x, 0.5, self.z))
        model = glm.rotate(model, self.rotation_y, glm.vec3(0.0, 1.0, 0.0))
        model = glm.scale(model, glm.vec3(1.0, 1.0, 1.0))
        return model