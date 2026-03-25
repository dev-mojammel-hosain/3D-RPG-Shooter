import glm
import math

class Projectile:
    def __init__(self, start_x, start_z, angle, speed=40.0):
        self.x = start_x
        self.z = start_z
        self.angle = angle
        
        self.speed = speed  
        self.lifespan = 2.0  
        self.age = 0.0
        
        # Calculate velocity based on the angle
        self.vel_x = math.sin(self.angle) * self.speed
        self.vel_z = math.cos(self.angle) * self.speed

    def update(self, delta_time):
        self.x += self.vel_x * delta_time
        self.z += self.vel_z * delta_time
        self.age += delta_time

    def get_model_matrix(self):
        model = glm.mat4(1.0)
        # Move the bullet up 1.0 unit on the Y-axis so it fires from the gun/roof height
        model = glm.translate(model, glm.vec3(self.x, 1.0, self.z))
        
        # Rotate the model to match the firing angle.
        model = glm.rotate(model, self.angle + math.pi, glm.vec3(0.0, 1.0, 0.0))
        
        # Scale the bullet massively so it's visible compared to the cars
        model = glm.scale(model, glm.vec3(4.0, 4.0, 4.0)) 
        return model