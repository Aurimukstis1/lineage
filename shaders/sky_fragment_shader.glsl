#version 330

//uniform sampler2D surface;

uniform float time;

out vec4 f_color;
in vec2 uv;

void main() {
  //vec4 color = texture(surface, uv);

  vec4 topColor =       vec4(0.4, 0.6, 0.8, 0.8);
  vec4 middleColor =    vec4(0.4, 0.6, 1.0, 1.0);
  vec4 bottomColor =    vec4(0.0, 0.0, 0.0, 1.0);

  vec4 color;
  if (uv.y < 0.5) {
    float t = uv.y / 0.5;
    color = mix(bottomColor, middleColor, t);
  } else {
    float t = (uv.y - 0.5) / 0.5;
    color = mix(middleColor, topColor, t);
  }

  //vec4 topColor =       vec4(0.5, 1.0, 1.0, 0.6);
  //vec4 bottomColor =    vec4(0.5, 0.0, 1.0, 1.0);

  // Use the y-coordinate of UV to interpolate between the top and bottom colors
  //vec4 color = mix(bottomColor, topColor, uv.y);

  f_color = color;
}