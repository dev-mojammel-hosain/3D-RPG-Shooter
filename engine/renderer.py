import OpenGL.GL as gl
import OpenGL.GL.shaders
import numpy as np
import glm
import ctypes

class Renderer:
    def __init__(self):
        self.shader_program = self._compile_shaders()
        self.vao, self.vertex_count = self._setup_test_floor()

        self.model_loc = gl.glGetUniformLocation(self.shader_program, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader_program, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader_program, "projection")
        self.color_loc = gl.glGetUniformLocation(self.shader_program, "objectColor")
        self.is_floor_loc = gl.glGetUniformLocation(self.shader_program, "isFloor")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader_program, "useTexture")
        
        self.light_dir_loc = gl.glGetUniformLocation(self.shader_program, "lightDir")
        self.light_color_loc = gl.glGetUniformLocation(self.shader_program, "lightColor")
        self.view_pos_loc = gl.glGetUniformLocation(self.shader_program, "viewPos")
        self.is_shadow_loc = gl.glGetUniformLocation(self.shader_program, "isShadow")

        gl.glEnable(gl.GL_DEPTH_TEST)
        
        # Enable Transparency for Shadows
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def load_texture(self, filepath):
        import pygame
        surface = pygame.image.load(filepath).convert_alpha()
        data = pygame.image.tobytes(surface, "RGBA", True)
        tex_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, surface.get_width(), surface.get_height(), 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        return tex_id

    def _compile_shaders(self):
        with open("shaders/default_vertex.glsl", "r") as f:
            vertex_src = f.read()
        with open("shaders/default_fragment.glsl", "r") as f:
            fragment_src = f.read()
        vertex_shader = gl.shaders.compileShader(vertex_src, gl.GL_VERTEX_SHADER)
        fragment_shader = gl.shaders.compileShader(fragment_src, gl.GL_FRAGMENT_SHADER)
        return gl.shaders.compileProgram(vertex_shader, fragment_shader)

    def _setup_test_floor(self):
        vertices = np.array([
            -0.5, 0.0, -0.5,  0.0, 0.0,  0.0, 1.0, 0.0,
             0.5, 0.0, -0.5,  1.0, 0.0,  0.0, 1.0, 0.0,
             0.5, 0.0,  0.5,  1.0, 1.0,  0.0, 1.0, 0.0,
             0.5, 0.0,  0.5,  1.0, 1.0,  0.0, 1.0, 0.0,
            -0.5, 0.0,  0.5,  0.0, 1.0,  0.0, 1.0, 0.0,
            -0.5, 0.0, -0.5,  0.0, 0.0,  0.0, 1.0, 0.0
        ], dtype=np.float32)
        vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(vao)
        vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, ctypes.c_void_p(20))
        gl.glEnableVertexAttribArray(2)
        
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)
        return vao, len(vertices) // 8

    def render(self, camera, model_matrix, color=(1.0, 1.0, 1.0), is_floor=False, custom_mesh=None, texture_id=None, is_shadow=False):
        gl.glUseProgram(self.shader_program)

        view_mat = camera.get_view_matrix()
        view_array = np.array(view_mat).astype(np.float32)
        proj_array = np.array(camera.get_projection_matrix()).astype(np.float32)
        model_array = np.array(model_matrix).astype(np.float32)

        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_TRUE, view_array)
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_TRUE, proj_array)
        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_TRUE, model_array)
        gl.glUniform3f(self.color_loc, color[0], color[1], color[2])
        gl.glUniform1i(self.is_floor_loc, int(is_floor))
        gl.glUniform1i(self.is_shadow_loc, int(is_shadow))

        gl.glUniform3f(self.light_dir_loc, -0.5, -1.0, -0.5)
        gl.glUniform3f(self.light_color_loc, 1.0, 1.0, 1.0)
        cam_pos = glm.inverse(view_mat)[3]
        gl.glUniform3f(self.view_pos_loc, cam_pos.x, cam_pos.y, cam_pos.z)

        if custom_mesh and texture_id is not None and not is_shadow:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
            gl.glUniform1i(self.use_tex_loc, 1)
        else:
            gl.glUniform1i(self.use_tex_loc, 0)

        vao_to_bind = custom_mesh.vao if custom_mesh else self.vao
        count_to_draw = custom_mesh.vertex_count if custom_mesh else self.vertex_count

        gl.glBindVertexArray(vao_to_bind)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, count_to_draw)
        gl.glBindVertexArray(0)