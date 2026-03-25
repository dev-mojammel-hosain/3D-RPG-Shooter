import math
import random

class Enemy:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.width = 2.0
        self.depth = 2.0
        self.health = 3
        self.color = (1.0, 1.0, 1.0)
        self.speed = 3.0
        
        # Give each enemy a random initial shot timer so they don't fire all at once
        self.shoot_timer = random.uniform(1.0, 3.0) 

    def update(self, delta_time, player_x, player_z):
        dx = player_x - self.x
        dz = player_z - self.z
        dist = math.hypot(dx, dz)

        # Stop moving if they get close enough to shoot
        if dist > 15.0: 
            self.x += (dx / dist) * self.speed * delta_time
            self.z += (dz / dist) * self.speed * delta_time

        # Tick down the timer
        self.shoot_timer -= delta_time

    def can_shoot(self):
        if self.shoot_timer <= 0:
            self.shoot_timer = 2.0 # Reset: Shoot once every 2 seconds
            return True
        return False