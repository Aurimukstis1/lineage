#version 330 core

in vec2 frag_texcoord;
out vec4 f_color;

uniform sampler2D surface;

void main() {
  f_color = texture(surface, frag_texcoord);
}