#version 330

in vec2 in_vert;
in vec2 in_texcoord;

out vec2 frag_texcoord;

void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);

    frag_texcoord = in_texcoord;
}