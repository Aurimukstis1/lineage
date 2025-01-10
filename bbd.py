import math
from array import array

import moderngl
import pygame

import moderngl_window

window_size = 1280, 720

def load_shader(file_path):
    with open(file_path, 'r') as file:
        return file.read()


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, color, height, width):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y

        self.image = pygame.Surface([width, height]) 
        self.image.fill(color)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def update(self):
        self.rect.x = window_size[0]//8
        self.rect.y = window_size[1]//8
        print(self.x)


class Bxox(pygame.sprite.Sprite):
    def __init__(self, x, y, color, height, width):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y

        self.image = pygame.Surface([width, height]) 
        self.image.fill(color)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x = self.x
        self.rect.y = self.y


class World():
    def __init__(self) -> None:
        self.entity_list = pygame.sprite.Group()
        
        self.player = Player(0,0,(255,100,100),32,16)

        self.entity_list.add(self.player)

        self.ground = Ground(0,0,16)
        self.ground.generate()

        box = Bxox(10,100,(255,255,255,255),64,64)
        self.entity_list.add(box)
    
    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.player.x -= 1
        if keys[pygame.K_RIGHT]:
            self.player.x += 1
        if keys[pygame.K_UP]:
            self.player.y += 1
        if keys[pygame.K_DOWN]:
            self.player.y -= 1

        self.player.update()
        self.entity_list.update()


class Ground():
    def __init__(self, x, y, length):
        self.x = x
        self.y = y
        self.length = length
        self.terrain = pygame.sprite.Group()

    def generate(self):
        i = 0
        while i < self.length:
            tile = Tile(16*i,self.y,1)
            self.terrain.add(tile)
            i=i+1


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, value):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.type = value

        self.image = pygame.image.load('Sprite-0001.png')
        self.image = pygame.transform.rotate(self.image, 180)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Pygame(moderngl_window.WindowConfig):
    title = "Lineage"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.wnd.name != "pygame2":
            raise RuntimeError("This example only works with --window pygame2 option")

        self.world = World()

        # The resolution of the pygame surface
        self.pg_res = window_size[0]//4,window_size[1]//4
        # Create a 24bit (rgba) offscreen surface pygame can render to
        self.pg_screen = pygame.Surface(self.pg_res, flags=pygame.SRCALPHA)
        # 32 bit (rgba) moderngl texture (4 channels, RGBA)
        self.pg_texture = self.ctx.texture(self.pg_res, 4)
        # Change the texture filtering to NEAREST for pixelated look.
        self.pg_texture.filter = moderngl.NEAREST, moderngl.NEAREST
        # The pygame surface is stored in BGRA format but RGBA
        # so we simply change the order of the channels of the texture
        self.pg_texture.swizzle = "BGRA"

        # Let's make a custom texture shader rendering the surface
        self.texture_program = self.ctx.program(
            vertex_shader = load_shader('vertex_shader.glsl'),
            fragment_shader = load_shader('fragment_shader.glsl')
        )
        self.texture_program["surface"] = 0

        buffer = self.ctx.buffer(
            data=array('f', [
                # Position (x, y) , Texture coordinates (x, y)
                -1.0, 1.0, 0.0, 1.0,  # upper left
                -1.0, -1.0, 0.0, 0.0,  # lower left
                1.0, 1.0, 1.0, 1.0,  # upper right
                1.0, -1.0, 1.0, 0.0,  # lower right
            ])
        )
        self.quad_fs = self.ctx.vertex_array(
            self.texture_program,
            [
                (
                    # The buffer containing the data
                    buffer,
                    # Format of the two attributes.
                    # - 2 floats for position
                    # - 2 floats for texture coordinates
                    "2f 2f",
                    # Names of the attributes in the shader program
                    "in_vert",
                    "in_texcoord",
                )
            ],
        )

    def on_render(self, time: float, frame_time: float):
        """Called every frame"""
        #self.texture_program["time"] = time

        self.world.update()

        self.render_pygame(time)

        self.ctx.clear(0,0,0)

        self.ctx.enable(moderngl.BLEND)
        self.pg_texture.use(location=0)
        self.quad_fs.render(mode=moderngl.TRIANGLE_STRIP)
        self.ctx.disable(moderngl.BLEND)

    def render_pygame(self, time: float):
        """Render to offscreen surface and copy result into moderngl texture"""
        self.pg_screen.fill((0, 0, 0, 0))
        
        pygame.draw.circle(self.pg_screen,(255,255,255,255),(100,100),10,1)
        pygame.draw.circle(self.pg_screen,(0,0,255,255),(0,100),10,1)
        pygame.draw.circle(self.pg_screen,(255,255,255,255),(100,0),10,1)
        pygame.draw.circle(self.pg_screen,(255,0,0,255),(0,0),10,1)

        # Draw entities and terrain
        for i in self.world.entity_list.sprites():
            if i != self.world.player:
                i.rect.x += self.world.player.x
                i.rect.y += self.world.player.y

        self.world.entity_list.draw(self.pg_screen)

        self.world.ground.terrain.draw(self.pg_screen)

        texture_data = self.pg_screen.get_view("1")
        self.pg_texture.write(texture_data)


if __name__ == "__main__":
    moderngl_window.run_window_config(Pygame, args=("--window", "pygame2"))