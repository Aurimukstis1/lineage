#version 330

uniform sampler2D surface;

out vec4 f_color;
in vec2 uv;

void main() {
  vec4 color = texture(surface, uv);

  color.r = color.r * 1.0;
  color.g = color.g * 1.0;
  color.b = color.b * 1.0;

  f_color = color;
}
