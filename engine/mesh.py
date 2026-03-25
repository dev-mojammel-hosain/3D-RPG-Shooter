import trimesh
import numpy as np
import OpenGL.GL as gl
import ctypes

class Mesh:
    def __init__(self, filepath):
        print(f"Loading 3D Model: {filepath}...")
        self.mesh = trimesh.load(filepath, force='mesh')

        # 1. Grab Vertices
        triangle_vertices = self.mesh.vertices[self.mesh.faces].reshape(-1, 3)
        
        # 2. Grab UVs
        if hasattr(self.mesh.visual, 'uv') and self.mesh.visual.uv is not None and len(self.mesh.visual.uv) > 0:
            triangle_uvs = self.mesh.visual.uv[self.mesh.faces].reshape(-1, 2)
        else:
            triangle_uvs = np.zeros((len(triangle_vertices), 2))

        # 3. --- NEW: Grab Normals (For Lighting) ---
        if hasattr(self.mesh, 'vertex_normals') and len(self.mesh.vertex_normals) > 0:
            triangle_normals = self.mesh.vertex_normals[self.mesh.faces].reshape(-1, 3)
        else:
            triangle_normals = np.zeros((len(triangle_vertices), 3))
            triangle_normals[:, 1] = 1.0 # Default point UP

        # Stack: [X,Y,Z,  U,V,  NX,NY,NZ] -> 8 floats per point
        vertex_data = np.hstack((triangle_vertices, triangle_uvs, triangle_normals)).astype(np.float32).flatten()
        self.vertex_count = len(vertex_data) // 8

        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)

        self.vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, gl.GL_STATIC_DRAW)

        # Tell GPU where Vertices are (Starts at 0)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        
        # Tell GPU where UVs are (Starts at 3)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        
        # --- NEW: Tell GPU where Normals are (Starts at 5) ---
        gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, 8 * 4, ctypes.c_void_p(20))
        gl.glEnableVertexAttribArray(2)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)