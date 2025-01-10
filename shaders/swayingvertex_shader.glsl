#version 330

in vec2 in_vert;
in vec2 in_texcoord;

out vec2 frag_texcoord;

uniform float time;
uniform float sway_amplitude;
uniform float sway_frequency;

// Function to generate a pseudo-random value based on input
float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

void main() {
    // Generate a random factor for this vertex based on its position
    float random_factor = random(in_vert);

    // Use the random factor to create a unique phase offset for each vertex
    float phase_offset = random_factor * in_vert.x * 3.14159; // Random phase [0, 2π]

    // Apply a sinusoidal wave with randomness to the x-coordinate of the vertex
    float sway = sin(time * sway_frequency + in_vert.y + phase_offset) * sway_amplitude;

    // Modify the x-position to create the sway effect
    vec2 swayed_position = in_vert + vec2(sway, sway/4.0);

    // Output the modified position
    gl_Position = vec4(swayed_position, 0.0, 1.0);

    // Pass the texture coordinate unchanged
    frag_texcoord = in_texcoord;
}