#version 330
// Vertex shader runs once for each vertex in geometry

//uniform float time;

in vec2 in_vert;
in vec2 in_texcoord;
out vec2 uv;

void main() {
  uv = in_texcoord;
  gl_Position = vec4(in_vert, 0.0, 1.0);
}