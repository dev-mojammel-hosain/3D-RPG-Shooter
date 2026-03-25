import glm
import math
import random

class Box:
    def __init__(self, start_x, start_z):
        self.x = start_x
        self.z = start_z
        
        # --- FIX: Made crates much bigger ---
        self.width = 2.0
        self.depth = 2.0
        
        self.health = 3
        self.color = (1.0, 1.0, 1.0) # White = Normal Texture
        
        # --- FIX: Random Rotation Angle ---
        self.rotation_y = random.uniform(0.0, math.pi * 2.0)

    def get_model_matrix(self):
        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(self.x, 0.5, self.z))
        model = glm.rotate(model, self.rotation_y, glm.vec3(0.0, 1.0, 0.0))
        # Scale the crate up
        model = glm.scale(model, glm.vec3(self.width, self.width, self.depth))
        return model