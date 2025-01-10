import math
from array import array

import moderngl
import pygame

import random

import moderngl_window

window_size = 1280, 720
res_downscale = 4

tile_size = 16, 16

camera_height_coef = 32

def load_shader(file_path):
    with open(file_path, 'r') as file:
        return file.read()


class Camera:
    def __init__(self, width, height):
        self.offset_x = 0
        self.offset_y = 0
        self.width = width
        self.height = height

    def update(self, target):
        # Center the camera on the target
        self.offset_x = target.x - self.width // 2
        self.offset_y = target.y - self.height // 2

    def apply(self, entity):
        # Apply the camera offset to an entity
        entity.rect.x -= self.offset_x
        entity.rect.y -= self.offset_y + camera_height_coef

    def apply_parallax(self, layer, dist):
        layer.rect.x -= self.offset_x / dist
        layer.rect.y -= self.offset_y + camera_height_coef

    def apply_group(self, group):
        for entity in group:
            self.apply(entity)

    def apply_parallax_group(self, group, dist):
        for layer in group:
            self.apply_parallax(layer, dist+1)


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
        self.rect.x = self.x
        self.rect.y = self.y


class World():
    def __init__(self):
        self.entity_list = pygame.sprite.Group()
        self.worldsize = 64
        
        self.ground = Ground(0,0,self.worldsize)
        self.ground.generate()

        self.background = Background(0,0,self.worldsize)
        self.background.generate()

        self.player = Player(0,16,(255,100,100),32,16)
        self.entity_list.add(self.player)

        self.camera = Camera(window_size[0] // res_downscale, window_size[1] // res_downscale)
    
    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.player.x -= 1
        if keys[pygame.K_RIGHT]:
            self.player.x += 1
        if keys[pygame.K_DOWN]:
            self.player.y -= 1
        if keys[pygame.K_UP]:
            self.player.y += 1

        self.player.update()
        self.ground.terrain.update()
        self.ground.under_terrain.update()
        self.ground.grass.update()
        self.background.flora.update()

        self.background.parallax_1.update()
        self.background.parallax_2.update()
        self.background.parallax_3.update()
        self.background.parallax_4.update()

        self.camera.update(self.player)


class Ground():
    def __init__(self, x, y, length):
        self.x = x
        self.y = y
        self.length = length
        self.terrain = pygame.sprite.Group()
        self.under_terrain = pygame.sprite.Group()
        self.grass = pygame.sprite.Group()

    def generate(self):
        i = 0
        while i < self.length:
            tile        = Tile(tile_size[0]*i,self.y,random.randrange(1,3))
            under_tile  = Tile(tile_size[0]*i,(self.y-tile_size[1]*4)+random.randrange(0,5),random.randrange(3,5))
            
            grass_tuft  = Foliage(random.randrange(0,self.length*tile_size[0]),tile_size[1],random.randrange(1,3))

            self.terrain.add(tile)
            self.under_terrain.add(under_tile)
            self.grass.add(grass_tuft)
            i=i+1


class Background():
    def __init__(self, x, y, length):
        self.x = x
        self.y = y
        self.length = length
        self.flora = pygame.sprite.Group()

        self.parallax_1 = pygame.sprite.Group()
        self.parallax_2 = pygame.sprite.Group()
        self.parallax_3 = pygame.sprite.Group()
        self.parallax_4 = pygame.sprite.Group()

    def generate(self):
        i = 0
        while i < self.length:
            indx = int((math.sin(2 * i) + math.sin(math.pi * i))*1.2)
            if indx > 0:
                tree  = Foliage(i*tile_size[0],tile_size[1],3)
                self.flora.add(tree)

            parallax_tile1 = ParallaxTile(i*64,16,1)
            parallax_tile2 = ParallaxTile(i*64,24,2)
            parallax_tile3 = ParallaxTile(i*64,32,3)
            parallax_tile4 = ParallaxTile(i*64,40,4)
            self.parallax_1.add(parallax_tile1)
            self.parallax_2.add(parallax_tile2)
            self.parallax_3.add(parallax_tile3)
            self.parallax_4.add(parallax_tile4)
            i=i+1


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, value):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.type = value

        if self.type == 1:
            self.image = pygame.image.load('Sprite-0001.png')
        if self.type == 2:
            self.image = pygame.image.load('Sprite-0002.png')
        if self.type == 3:
            self.image = pygame.image.load('Sprite-2002.png')
        if self.type == 4:
            self.image = pygame.image.load('Sprite-2002.png')
        
        self.image = pygame.transform.rotate(self.image, 180)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def update(self):
        self.rect.x = self.x
        self.rect.y = self.y


class Foliage(pygame.sprite.Sprite):
    def __init__(self, x, y, value):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.type = value

        if self.type == 1:
            self.image = pygame.image.load('Sprite-01.png')
        if self.type == 2:
            self.image = pygame.image.load('Sprite-02.png')
        if self.type == 3:
            self.image = pygame.image.load('Sprite-001.png')
        
        self.image = pygame.transform.rotate(self.image, 180)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x = self.x
        self.rect.y = self.y


class ParallaxTile(pygame.sprite.Sprite):
    def __init__(self, x, y, dist):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.dist = dist+1

        #if dist == 2:
        #    self.image = pygame.image.load('Sprite-1112.png')
        #if dist == 3:
        #    self.image = pygame.image.load('Sprite-1112.png')
        #if dist == 4:
        #    self.image = pygame.image.load('Sprite-1112.png')
        #if dist == 5:
        #    self.image = pygame.image.load('Sprite-1112.png')

        self.image = pygame.image.load('Sprite-1112.png')

        self.image = pygame.transform.rotate(self.image, 180)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x = self.x
        self.rect.y = self.y


class Pygame(moderngl_window.WindowConfig):
    title = "Lineage"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.wnd.name != "pygame2":
            raise RuntimeError("This example only works with --window pygame2 option")

        self.world = World()

        self.pg_res = window_size[0]//res_downscale,window_size[1]//res_downscale

        self.pg_screen = pygame.Surface(self.pg_res, flags=pygame.SRCALPHA)
        self.pg_texture = self.ctx.texture(self.pg_res, 4)
        self.pg_texture.filter = moderngl.NEAREST, moderngl.NEAREST
        self.pg_texture.swizzle = "BGRA"

        self.foliage_surface = pygame.Surface(self.pg_res, flags=pygame.SRCALPHA)
        self.foliage_texture = self.ctx.texture(self.pg_res, 4)
        self.foliage_texture.filter = moderngl.NEAREST, moderngl.NEAREST
        self.foliage_texture.swizzle = "BGRA"

        # Let's make a custom texture shader rendering the surface
        self.texture_program = self.ctx.program(
            vertex_shader = load_shader('shaders/vertex_shader.glsl'),
            fragment_shader = load_shader('shaders/fragment_shader.glsl')
        )
        self.texture_program["surface"] = 0

        self.swaying_texture_program = self.ctx.program(
            vertex_shader=load_shader('shaders/swayingvertex_shader.glsl'),
            fragment_shader=load_shader('shaders/swayingfragment_shader.glsl')
        )
        self.swaying_texture_program["surface"] = 0

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
                    buffer,
                    "2f 2f",
                    "in_vert",
                    "in_texcoord",
                )
            ],
        )
        self.quad_fs2 = self.ctx.vertex_array(
            self.swaying_texture_program,
            [
                (
                    buffer,
                    "2f 2f",
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

        self.swaying_texture_program["time"] = time
        self.swaying_texture_program["sway_amplitude"] = 0.02
        self.swaying_texture_program["sway_frequency"] = 0.5

        self.pg_texture.use         (location=0)
        self.quad_fs.render         (mode=moderngl.TRIANGLE_STRIP)
        self.foliage_texture.use    (location=0)
        self.quad_fs2.render        (mode=moderngl.TRIANGLE_STRIP)

        self.ctx.disable(moderngl.BLEND)

    def render_pygame(self, time: float):
        """Render to offscreen surface and copy result into moderngl texture"""
        self.pg_screen.fill((10, 150, 220, 255))

        self.foliage_surface.fill((0, 0, 0, 0))

        pygame.draw.rect(self.pg_screen,(32,30,48,255),(0,(tile_size[1]*-2-camera_height_coef),1000,100),0)

        # Transform entities and whatever
        self.world.camera.apply_group(self.world.entity_list)
        self.world.camera.apply_group(self.world.ground.terrain)
        self.world.camera.apply_group(self.world.ground.under_terrain)
        self.world.camera.apply_group(self.world.ground.grass)
        self.world.camera.apply_group(self.world.background.flora)

        self.world.camera.apply_parallax_group(self.world.background.parallax_1,1)
        self.world.camera.apply_parallax_group(self.world.background.parallax_2,2)
        self.world.camera.apply_parallax_group(self.world.background.parallax_3,3)
        self.world.camera.apply_parallax_group(self.world.background.parallax_4,4)

        # Draw entities and tiles
        self.world.background.parallax_4.draw(self.pg_screen)
        self.world.background.parallax_3.draw(self.pg_screen)
        self.world.background.parallax_2.draw(self.pg_screen)
        self.world.background.parallax_1.draw(self.pg_screen)

        self.world.background.flora.draw(self.foliage_surface)

        self.world.ground.terrain.draw(self.pg_screen)
        self.world.ground.under_terrain.draw(self.pg_screen)
        self.world.ground.grass.draw(self.pg_screen)
        self.world.entity_list.draw(self.pg_screen)
        
        foliage_data = self.foliage_surface.get_view("1")
        self.foliage_texture.write(foliage_data)

        texture_data = self.pg_screen.get_view("1")
        self.pg_texture.write(texture_data)


if __name__ == "__main__":
    moderngl_window.run_window_config(Pygame, args=("--window", "pygame2"))