import glm

class Camera:
    def __init__(self, screen_width, screen_height):
        # The physical position of the camera in the sky
        self.position = glm.vec3(0.0, 10.0, 10.0)
        
        # The point on the ground the camera is currently looking at
        self.target = glm.vec3(0.0, 0.0, 0.0)
        
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.zoom = 15.0 
        self.update_projection(screen_width, screen_height)

        # --- NEW CAMERA SETTINGS ---
        self.deadzone = 2.0      # The size of the invisible square threshold
        self.smooth_speed = 5.0  # How fast the camera catches up (higher = stiffer)

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.target, self.up)

    def update_projection(self, width, height):
        aspect = width / height
        self.projection_matrix = glm.ortho(
            -self.zoom * aspect, self.zoom * aspect, 
            -self.zoom, self.zoom, 
            0.1, 100.0
        )

    def get_projection_matrix(self):
        return self.projection_matrix

    def follow_target(self, player_x, player_z, delta_time):
        # 1. Find the distance between the player and where the camera is currently looking
        dist_x = player_x - self.target.x
        dist_z = player_z - self.target.z

        # 2. Determine the "Ideal" focus point (it only changes if player leaves the deadzone box)
        ideal_x = self.target.x
        ideal_z = self.target.z

        if dist_x > self.deadzone:
            ideal_x = player_x - self.deadzone
        elif dist_x < -self.deadzone:
            ideal_x = player_x + self.deadzone

        if dist_z > self.deadzone:
            ideal_z = player_z - self.deadzone
        elif dist_z < -self.deadzone:
            ideal_z = player_z + self.deadzone

        # 3. Apply Linear Interpolation (Lerp) for that smooth easing effect!
        lerp_factor = self.smooth_speed * delta_time
        
        self.target.x += (ideal_x - self.target.x) * lerp_factor
        self.target.z += (ideal_z - self.target.z) * lerp_factor

        # 4. Move the physical camera to match this new smoothed target
        self.position.x = self.target.x
        self.position.z = self.target.z + 10.0