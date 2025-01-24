#version 330 core

uniform sampler2D surface;

in vec2 frag_texcoord;
out vec4 f_color;

vec2 vv;

void main() {
  vv = frag_texcoord;

  ///vv.x += cos(vv.y*10.0+time)/200.0;

  f_color = texture(surface, vv);
}