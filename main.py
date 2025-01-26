import math
from array import array
import moderngl
import pygame
import random
import moderngl_window
import perlin_noise
import time as taime
import cProfile

window_size = 1920, 1080
res_downscale = 4
tile_size = 16, 16
camera_height_coef = 48


def load_shader(file_path):
    with open(file_path, 'r') as file:
        return file.read()


class Camera:
    def __init__(self, width, height):
        self.offset_x   = 0
        self.offset_y   = 0
        self.width      = width
        self.height     = height
        # --- --- ---

    def update(self, target):
        # centering the camera to the target (usually player)
        self.offset_x = target.x - (self.width // 2 - 8)
        self.offset_y = target.y - self.height // 2

    def apply(self, entity):
        # apply the difference between the target and whatever entity
        entity.rect.x -= self.offset_x
        entity.rect.y -= self.offset_y + camera_height_coef

    def apply_parallax(self, layer, dist, cloud):
        if cloud == True:
            if dist == 6:
                layer.rect.x -= self.offset_x // (dist*5)
            else:
                layer.rect.x -= self.offset_x // (dist*3)
            layer.rect.y -= self.offset_y + camera_height_coef
        else:
            if dist == 6:
                layer.rect.x -= self.offset_x // (dist*4)
            else:
                layer.rect.x -= self.offset_x // (dist*2)
            layer.rect.y -= self.offset_y + camera_height_coef

    def apply_to_group(self, group):
        for entity in group:
            self.apply(entity)

    def apply_to_parallax_group(self, group, dist, cloud=False):
        for layer in group:
            self.apply_parallax(layer, dist, cloud)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, color, height, width):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.coincount = 24

        self.image = pygame.Surface([width, height]) 
        self.image.fill(color)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def update(self):
        self.rect.x = self.x
        self.rect.y = self.y

    def givecoin(self):
        self.coincount+=1

    def takecoin(self):
        self.coincount-=1


class NPC():
    # --- #
    class NPC_builder(pygame.sprite.Sprite):
        def __init__(self, x, y, color, height, width):
            pygame.sprite.Sprite.__init__(self)
            self.id = random.randrange(1000,10000)
            self.x = x
            self.y = y
            self.assigned_task = None
            self.assigned_task_id = 0
            self.wandering = True
            self.direction = 1
            self.timer = 360

            self.walking_left = False

            self.image = pygame.Surface([width, height]) 
            self.image.fill(color)
            
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y
        
        def update(self):
            self.rect.x = self.x
            self.rect.y = self.y

            if self.assigned_task:
                self.wandering = False
                if self.assigned_task.x < self.x:
                    self.x -= 0.25
                elif self.assigned_task.x > self.x:
                    self.x += 0.25
            else:
                self.wandering = True
                self.timer -= 1

                if self.timer <= 0:
                    self.direction = random.randrange(-1,2)
                    if self.direction is 0:
                        self.timer = 360
                    else:
                        self.timer = 360
                
                if self.direction is -1:
                    self.x -= 0.05
                if self.direction is 1:
                    self.x += 0.05


class World():
    def __init__(self):
        self.entity_list = pygame.sprite.Group()
        self.WORKER_LIST = []
        self.TASK_QUEUE  = []

        self.PROMISE_QUEUE=[]

        self.worldsize = 1024
        self.inertia = 0.0
        
        self.ground = Ground(0,0,self.worldsize)
        self.structures = Structures(0,0)
        self.background = Background(0,0,self.worldsize)

        self.ground.generate()
        self.background.generate()

        self.player = Player((self.worldsize*tile_size[0])//2,16,(100,0,150),32,16)
        self.entity_list.add(self.player)

        self.npc_example_1 = NPC.NPC_builder((self.worldsize//2)*tile_size[0],16,(150,150,150),16,16)
        self.entity_list.add(self.npc_example_1)
        self.npc_example_2 = NPC.NPC_builder((self.worldsize//2)*tile_size[0],16,(200,200,200),16,16)
        self.entity_list.add(self.npc_example_2)
        self.npc_example_3 = NPC.NPC_builder((self.worldsize//2)*tile_size[0],16,(165,165,165),16,16)
        self.entity_list.add(self.npc_example_3)
        self.WORKER_LIST.append(self.npc_example_1)
        self.WORKER_LIST.append(self.npc_example_2)
        self.WORKER_LIST.append(self.npc_example_3)

        for i in self.ground.foliage:
            if i.x >= self.structures.hub.x-128 and i.x <= self.structures.hub.x+128:
                i.kill()

        self.ground.combination_foliage = [
            i for i in self.ground.combination_foliage 
            if not (self.structures.hub.x - 256 <= i.x <= self.structures.hub.x + 256)
        ]

        for i in range(0,self.worldsize*tile_size[0],16*tile_size[0]):
            if i < self.structures.hub.x:
                if not i > self.structures.hub.x-256:
                    self.wall_example = Structures.Wall(i,16,"left")
                    self.structures.structure_list.add(self.wall_example)
            elif i > self.structures.hub.x:
                if not i < self.structures.hub.x+256:
                    self.wall_example = Structures.Wall(i,16,"right")
                    self.structures.structure_list.add(self.wall_example)
        else:
            print("[WORLD] O- Walls generated ...")

        self.camera = Camera(window_size[0] // res_downscale, window_size[1] // res_downscale)

    
    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LSHIFT]==False:
            if keys[pygame.K_LEFT]:
                if not self.inertia < -0.5:
                    self.inertia -= 0.025
            if keys[pygame.K_RIGHT]:
                if not self.inertia > 0.5:
                    self.inertia += 0.025
        else:
            if keys[pygame.K_LEFT]:
                if not self.inertia < -1.0:
                    self.inertia -= 0.05
            if keys[pygame.K_RIGHT]:
                if not self.inertia > 1.0:
                    self.inertia += 0.05
        
        self.player.x += self.inertia

        self.inertia = self.inertia / 1.05

        self.entity_list.update()
        self.ground.terrain.update()
        self.ground.under_terrain.update()
        self.ground.foliage.update()
        for i in self.ground.combination_foliage[:]:
            i.parts.update()
        self.structures.updater(self.player)
        self.structures.structure_list.update()

        self.background.parallax_layer_2.update()
        self.background.parallax_layer_3.update()
        self.background.parallax_layer_4.update()
        self.background.parallax_layer_5.update()
        self.background.parallax_layer_6.update()

        self.background.weather_layer_4.update()
        self.background.weather_layer_5.update()
        self.background.weather_layer_6.update()

        for i in self.background.weather_layer_4:
            i.x += 0.01
            if i.x > self.worldsize*(tile_size[0]//4):
                i.x = 0
        for i in self.background.weather_layer_5:
            i.x += 0.005
            if i.x > self.worldsize*(tile_size[0]//4):
                i.x = 0
        for i in self.background.weather_layer_6:
            i.x += 0.001
            if i.x > self.worldsize*(tile_size[0]//4):
                i.x = 0

        self.camera.update(self.player)

        for worker in self.WORKER_LIST:

            x = 0
            for building_project in self.structures.structure_list:
                if worker.assigned_task_id == building_project.assigned_task_id:
                    x += 1

            if x == 0:
                worker.assigned_task_id = 0
                worker.assigned_task = None
                print("TASK FREED")


        for building_project in self.structures.structure_list:
            if building_project.target_progress > building_project.progress and building_project.queued == False:
                self.TASK_QUEUE.append(building_project)
                building_project.queued = True

        # if self.TASK_QUEUE:
        #     print("O- TASKS IN QUEUE ...")
        #     print("O- LOOPING THROUGH TASK QUEUE ...")
        #     for task in self.TASK_QUEUE:
        #         print("O- LOOKING FOR FREE WORKER ...")
        #         for i in self.WORKER_LIST:
        #             if i.assigned_task == None:
        #                 random_id = random.randrange(1000,10000)
        #                 print("O- FOUND FREE WORKER ...")
        #                 i.assigned_task = task
        #                 i.assigned_task_id = random_id
        #                 task.assigned_task_id = random_id
        #                 print("O- ASSIGNED TASK ...")
        #                 self.TASK_QUEUE.remove(task)
        #                 break
        #             else:
        #                 print("X- worker taken ...")

        if self.TASK_QUEUE:
            print("O- TASKS IN QUEUE ...")
            print("O- LOOPING THROUGH TASK QUEUE ...")
            for task in self.TASK_QUEUE:
                print("O- LOOKING FOR FREE WORKER ...")
                print("O- CREATING LIST OF DISTANCES TO WORKERS ...")
                
                distance_list = []
                corresponding_worker_list = []

                for worker in self.WORKER_LIST:
                    if worker.assigned_task is None:
                        distance = abs(worker.x - task.x)
                        distance_list.append(distance)
                        corresponding_worker_list.append(worker)
                    else:
                        print("X- Worker taken ...")

                print("O- FINDING CLOSEST WORKER TO TASK ...")
                if distance_list:
                    random_id = random.randrange(1000,10000)
                    min_distance_index = distance_list.index(min(distance_list))
                    closest_worker = corresponding_worker_list[min_distance_index]
                    print(f"O- Assigning task at x={task.x} to worker at x={closest_worker.x}")
                    closest_worker.assigned_task = task
                    closest_worker.assigned_task_id = random_id
                    task.assigned_task_id = random_id
                    print("O- ASSIGNED TASK ... "+str(random_id))
                    self.TASK_QUEUE.remove(task)
                else:
                    print("X- No available workers for this task.")


        for building_project in self.structures.structure_list:
            for worker in self.WORKER_LIST:
                if worker.x >= building_project.x-16 and worker.x <= building_project.x+16:
                    if building_project.queued:
                        if building_project.assigned_task_id is worker.assigned_task_id:
                            building_project.build()


class Ground():
    def __init__(self, x, y, length):
        self.x = x
        self.y = y
        self.length = length
        self.terrain = pygame.sprite.Group()
        self.under_terrain = pygame.sprite.Group()

        self.foliage = pygame.sprite.Group()
        self.combination_foliage = []

    def generate(self):
        i=0
        while i < self.length:
            indx = random.randrange(-1,2)
            tile        = Tile(tile_size[0]*i,self.y,random.randrange(1,3))
            under_tile  = Tile(tile_size[0]*i,(self.y-tile_size[1]*4)+random.randrange(0,5),random.randrange(3,5))
            grass_tuft  = Foliage.Grass1(random.randrange(0,self.length*tile_size[0]),tile_size[1])

            if indx >= 1:
                displacement = (i*tile_size[0])-random.randrange(-10,10)
                tree  = Foliage.Tree1(displacement,tile_size[1])
                self.combination_foliage.append(tree)
                
            self.terrain.add        (tile)
            self.under_terrain.add  (under_tile)
            self.foliage.add        (grass_tuft)
            i=i+1


class Background():
    def __init__(self, x, y, length):
        self.x = x
        self.y = y
        self.length = length

        self.parallax_layer_2 = pygame.sprite.Group()
        self.parallax_layer_3 = pygame.sprite.Group()
        self.parallax_layer_4 = pygame.sprite.Group()
        self.parallax_layer_5 = pygame.sprite.Group()
        self.parallax_layer_6 = pygame.sprite.Group() 

        self.weather_layer_4  = pygame.sprite.Group()
        self.weather_layer_5  = pygame.sprite.Group()
        self.weather_layer_6  = pygame.sprite.Group()

    def generate(self):
        i = 0

        parallax_tile_6 = ParallaxTile(self.length/2,48,6)
        self.parallax_layer_6.add(parallax_tile_6)
        aoffset = 64

        while i < self.length/16:
            indx = random.randrange(-5,2)
            if indx >= 1:
                cloud_instance_4 = Cloud(tile_size[0]*i,100,2)
                self.weather_layer_4.add(cloud_instance_4)
            indx = random.randrange(-5,2)
            if indx >= 1:
                cloud_instance_5 = Cloud(tile_size[0]*i,90,2)
                self.weather_layer_5.add(cloud_instance_5)
            indx = random.randrange(-5,2)
            if indx >= 1:
                cloud_instance_6 = Cloud(tile_size[0]*i,80,6)
                self.weather_layer_6.add(cloud_instance_6)

            parallax_tile_2 = ParallaxTile((i*64)-aoffset,16,2)
            parallax_tile_3 = ParallaxTile((i*64)-aoffset,24,3)
            parallax_tile_4 = ParallaxTile((i*64)-aoffset,32,4)
            parallax_tile_5 = ParallaxTile((i*64)-aoffset,40,5)
            
            self.parallax_layer_2.add(parallax_tile_2)
            self.parallax_layer_3.add(parallax_tile_3)
            self.parallax_layer_4.add(parallax_tile_4)
            self.parallax_layer_5.add(parallax_tile_5)
            i=i+1


class Cloud(pygame.sprite.Sprite):
    def __init__(self, x, y, dist):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.dist = dist
    
        self.image = pygame.image.load('cloudpng.png') 
        self.image = pygame.transform.rotate(self.image,180)
        self.image = pygame.transform.scale(self.image,(64-random.randrange(-10,10),32-random.randrange(-10,10)))

        if dist == 6:
            self.image = pygame.image.load('s_cloud_6.png') 
            self.image = pygame.transform.rotate(self.image,180)
            self.image = pygame.transform.scale(self.image,(96-random.randrange(-20,20),48-random.randrange(-20,20)))
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def update(self):
        self.rect.x = self.x
        self.rect.y = self.y


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


class Foliage():
    class Tree1():
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.parts = pygame.sprite.Group()

            self.trunk = Foliage.TreeTrunk1(self.x,self.y)
            self.leaves = Foliage.TreeLeaves1(self.x-24,self.y+64)

            self.parts.add(self.trunk)
            self.parts.add(self.leaves)

    class Grass1(pygame.sprite.Sprite):
        def __init__(self, x, y):
            pygame.sprite.Sprite.__init__(self)
            self.x = x
            self.y = y
            self.index = 0
            self.superdex=0

            self.image = pygame.image.load('s_grass_01-0.png')
            self.image = pygame.transform.flip(self.image,False,True)

            self.images = {
                0: pygame.image.load('s_grass_01-0.png'),
                1: pygame.image.load('s_grass_01-1.png'),
                2: pygame.image.load('s_grass_01-2.png'),
                3: pygame.image.load('s_grass_01-3.png'),
                4: pygame.image.load('s_grass_01-4.png'),
                5: pygame.image.load('s_grass_01-5.png')
            }

            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y

        def update(self):
            self.rect.x = self.x
            self.rect.y = self.y

            self.image = pygame.transform.flip(self.images[self.index], False, True)

            if self.superdex == 30:
                self.superdex = 0
                if self.index == 5:
                    self.index = 0
                else:
                    self.index += 1
            else:
                self.superdex += 1

    class Grass2(pygame.sprite.Sprite):
        def __init__(self, x, y):
            pygame.sprite.Sprite.__init__(self)
            self.x = x
            self.y = y
            self.index = 0
            self.superdex=0

            self.image = pygame.image.load('s_grass_02-0.png')
            self.image = pygame.transform.flip(self.image,False,True)

            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y

        def update(self):
            self.rect.x = self.x
            self.rect.y = self.y

            self.image = pygame.image.load('s_grass_02-'+str(self.index)+'.png')
            self.image = pygame.transform.flip(self.image,False,True)

            if self.superdex == 30:
                self.superdex = 0
                if self.index == 5:
                    self.index = 0
                else:
                    self.index += 1
            else:
                self.superdex += 1

    class TreeLeaves1(pygame.sprite.Sprite):
        def __init__(self, x, y):
            pygame.sprite.Sprite.__init__(self)
            self.x = x
            self.y = y
            self.index = 0 + random.randrange(1,5)
            self.superdex=0

            self.image = pygame.image.load('s_tree_leaves_01-0.png')
            self.image = pygame.transform.flip(self.image,False,True)

            self.images = {
                0: pygame.image.load('s_tree_leaves_01-0.png'),
                1: pygame.image.load('s_tree_leaves_01-1.png'),
                2: pygame.image.load('s_tree_leaves_01-2.png'),
                3: pygame.image.load('s_tree_leaves_01-3.png'),
                4: pygame.image.load('s_tree_leaves_01-4.png'),
                5: pygame.image.load('s_tree_leaves_01-5.png')
            }

            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y

        def update(self):
            self.rect.x = self.x
            self.rect.y = self.y

            self.image = pygame.transform.flip(self.images[self.index], False, True)

            if self.superdex == 60:
                self.superdex = 0
                if self.index == 5:
                    self.index = 0
                else:
                    self.index += 1
            else:
                self.superdex += 1

    class TreeTrunk1(pygame.sprite.Sprite):
        def __init__(self, x, y):
            pygame.sprite.Sprite.__init__(self)
            self.x = x
            self.y = y

            self.image = pygame.image.load('s_tree_trunk_02-0.png')
            self.image = pygame.transform.flip(self.image,False,True)

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
        self.dist = dist

        if self.dist == 2:
            self.image = pygame.image.load('Sprite-1113.png')
            self.image.fill((10,10,20,0),special_flags=pygame.BLEND_RGB_ADD)
        if self.dist == 3:
            self.image = pygame.image.load('Sprite-1112.png')
            self.image.fill((20,20,30,0),special_flags=pygame.BLEND_RGB_ADD)
        if self.dist == 4:
            self.image = pygame.image.load('Sprite-1112.png')
            self.image.fill((30,30,40,0),special_flags=pygame.BLEND_RGB_ADD)
        if self.dist == 5:
            self.image = pygame.image.load('Sprite-1111.png')
            self.image.fill((40,40,50,0),special_flags=pygame.BLEND_RGB_ADD)
        if self.dist == 6:
            self.image = pygame.image.load('Sprite-1116.png')
            self.image.fill((50,50,50,0),special_flags=pygame.BLEND_RGB_ADD)

        self.image = pygame.transform.rotate(self.image, 180)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x = self.x
        self.rect.y = self.y


class Structures():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.structure_list = pygame.sprite.Group()

        self.hub = Hub((1024*tile_size[0])//2,16)
        self.hub_left_wall = self.Wall(((1024*tile_size[0])//2)-256,16,"left")
        self.hub_right_wall= self.Wall(((1024*tile_size[0])//2)+256,16,"right")
        self.hub_builder_stand = self.Builder_stand(((1024*tile_size[0])//2)+128,16,"right")
        self.hub_archer_stand  = self.Archer_stand(((1024*tile_size[0])//2)-128,16,"left")
        self.structure_list.add(self.hub)
        self.structure_list.add(self.hub_left_wall)
        self.structure_list.add(self.hub_right_wall)
        self.structure_list.add(self.hub_builder_stand)
        self.structure_list.add(self.hub_archer_stand)
        print("Location of campfire: "+str(128*tile_size[0]//2))

    def updater(self, input_target):
        for i in self.structure_list:
            i.check(input_target)

    class Wall(pygame.sprite.Sprite):
        def __init__(self, x, y, left_or_right):
            pygame.sprite.Sprite.__init__(self)
            self.x = x
            self.y = y
            self.assigned_builder = False
            self.target_progress = 0
            self.build_progress = 0.0
            self.progress = 0
            self.heldcounter = 60
            self.queued = False
            self.assigned_task_id = 0
            self.left_or_right = left_or_right

            self.images = {
                0: pygame.image.load('s_wall_0-0.png'),
                1: pygame.image.load('s_wall_0-1.png'),
                2: pygame.image.load('s_wall_0-2.png')
            }

            self.image = self.images[self.progress]
            self.image = pygame.transform.flip(self.image, False, True)

            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y

        def update(self):
            self.rect.x = self.x - self.image.get_width()/2
            self.rect.y = self.y

            if self.build_progress >= 1.0:
                self.progress += 1
                self.build_progress = 0.0
                self.assigned_task_id = 0
                self.queued = False
                self.assigned_builder = False

        def build(self):
            if self.progress < 2:
                if self.build_progress < 1.0:
                    self.build_progress += 0.01
            
                print("Building ...")

        def check(self, target):
            keys = pygame.key.get_pressed()
            
            if self.left_or_right == "left":
                self.image = pygame.transform.flip(self.images[self.progress], False, True)
            else:
                self.image = pygame.transform.flip(self.images[self.progress], True, True)

            if self.x >= target.x-32 and self.x <= target.x+32:
                self.image.fill((10,10,10,0),special_flags=pygame.BLEND_RGB_ADD)

                if keys[pygame.K_DOWN]:
                    self.heldcounter -= 1

                    if self.heldcounter <= 0:
                        self.target_progress += 1
                        self.heldcounter = 60

                        print("Upgraded wall "+str(self.x)+" "+str(self.y))

                else:
                    self.heldcounter = 60

    class Builder_stand(pygame.sprite.Sprite):
        def __init__(self, x, y, left_or_right):
            pygame.sprite.Sprite.__init__(self)
            self.x = x
            self.y = y
            self.left_or_right = left_or_right
            # --- #
            self.assigned_builder = False
            self.target_progress = 0
            self.build_progress = 0.0
            self.progress = 0
            self.heldcounter = 60
            self.queued = False
            self.assigned_task_id = 0
            # --- #

            self.image = pygame.image.load('s_builder_stand.png')
            self.image = pygame.transform.flip(self.image, False, True)

            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y

        def update(self):
            self.rect.x = self.x - self.image.get_width()/2
            self.rect.y = self.y

        def check(self, target):
            keys = pygame.key.get_pressed()

            self.image = pygame.image.load('s_builder_stand.png')
            
            if self.left_or_right == "left":
                self.image = pygame.transform.flip(self.image, False, True)
            else:
                self.image = pygame.transform.flip(self.image, True, True)

            if self.x >= target.x-32 and self.x <= target.x+32:
                self.image.fill((10,10,10,0),special_flags=pygame.BLEND_RGB_ADD)

    class Archer_stand(pygame.sprite.Sprite):
        def __init__(self, x, y, left_or_right):
            pygame.sprite.Sprite.__init__(self)
            self.x = x
            self.y = y
            self.left_or_right = left_or_right
            # --- #
            self.assigned_builder = False
            self.target_progress = 0
            self.build_progress = 0.0
            self.progress = 0
            self.heldcounter = 60
            self.queued = False
            self.assigned_task_id = 0
            # --- #

            self.image = pygame.image.load('s_archer_stand.png')
            self.image = pygame.transform.flip(self.image, False, True)

            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y

        def update(self):
            self.rect.x = self.x - self.image.get_width()/2
            self.rect.y = self.y

        def check(self, target):
            keys = pygame.key.get_pressed()

            self.image = pygame.image.load('s_archer_stand.png')
            
            if self.left_or_right == "left":
                self.image = pygame.transform.flip(self.image, False, True)
            else:
                self.image = pygame.transform.flip(self.image, True, True)

            if self.x >= target.x-32 and self.x <= target.x+32:
                self.image.fill((10,10,10,0),special_flags=pygame.BLEND_RGB_ADD)


class Hub(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.progress = 0
        self.target_progress = 0
        self.heldcounter = 120
        self.queued = False
        self.assigned_task_id = 0

        self.images = {
            0: pygame.image.load('s_campfire_unlit-0.png'),
            1: pygame.image.load('s_campfire_unlit-1.png'),
            2: pygame.image.load('s_campfire_unlit-2.png'),
            3: pygame.image.load('s_campfire_unlit-3.png')
        }

        self.image = self.images[self.progress]
        self.image = pygame.transform.flip(self.image, False, True)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x = self.x - self.image.get_width()/2
        self.rect.y = self.y

    def check(self, target):
        keys = pygame.key.get_pressed()

        self.image = pygame.transform.flip(self.images[self.progress], False, True)

        if self.x >= target.x-32 and self.x <= target.x+32:
            self.image.fill((10,10,10,0),special_flags=pygame.BLEND_RGB_ADD)

            if keys[pygame.K_DOWN]:
                self.heldcounter -= 1

                if self.heldcounter <= 0:
                    if not self.progress >= 3:
                        if target.coincount >= self.progress*3:
                            self.progress += 1
                            target.coincount -= self.progress*3
                            self.heldcounter = 120

            else:
                self.heldcounter = 120
    
    def build(self):
        pass


class Pygame(moderngl_window.WindowConfig):
    title = "Lineage"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.wnd.name != "pygame2":
            raise RuntimeError("This example only works with --window pygame2 option")

        self.world = World()

        self.main_res = window_size[0]//res_downscale,window_size[1]//res_downscale

        self.main_surface = pygame.Surface(self.main_res, flags=pygame.SRCALPHA)
        self.main_texture = self.ctx.texture(self.main_res, 4)
        self.main_texture.filter = moderngl.NEAREST, moderngl.NEAREST
        self.main_texture.swizzle = "BGRA"

        self.foliage_surface = pygame.Surface(self.main_res, flags=pygame.SRCALPHA)
        self.foliage_texture = self.ctx.texture(self.main_res, 4)
        self.foliage_texture.filter = moderngl.NEAREST, moderngl.NEAREST
        self.foliage_texture.swizzle = "BGRA"

        self.sky_surface = pygame.Surface(self.main_res, flags=pygame.SRCALPHA)
        self.sky_texture = self.ctx.texture(self.main_res, 4)
        self.sky_texture.filter = moderngl.NEAREST, moderngl.NEAREST
        self.sky_texture.swizzle = "BGRA"

        # Let's make a custom texture shader rendering the surface
        self.main_texture_program = self.ctx.program(
            vertex_shader=load_shader   ('shaders/main_vertex_shader.glsl'),
            fragment_shader=load_shader ('shaders/main_fragment_shader.glsl')
        )
        self.foliage_texture_program = self.ctx.program(
            vertex_shader=load_shader   ('shaders/swaying_vertex_shader.glsl'),
            fragment_shader=load_shader ('shaders/swaying_fragment_shader.glsl')
        )
        self.sky_texture_program = self.ctx.program(
            vertex_shader=load_shader   ('shaders/sky_vertex_shader.glsl'),
            fragment_shader=load_shader ('shaders/sky_fragment_shader.glsl')
        )

        self.main_texture_program   ["surface"] = 0
        self.foliage_texture_program["surface"] = 0

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
            self.main_texture_program,
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
            self.foliage_texture_program,
            [
                (
                    buffer,
                    "2f 2f",
                    "in_vert",
                    "in_texcoord",
                )
            ],
        )
        self.quad_sky = self.ctx.vertex_array(
            self.sky_texture_program,
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
        self.world.update()

        self.render_pygame(time)

        self.ctx.clear(0,0,0)
        self.ctx.enable(moderngl.BLEND)

        self.sky_texture.use        (location=0)
        self.quad_sky.render        (mode=moderngl.TRIANGLE_STRIP)
        self.main_texture.use       (location=0)
        self.quad_fs.render         (mode=moderngl.TRIANGLE_STRIP)
        self.foliage_texture.use    (location=0)
        self.quad_fs2.render        (mode=moderngl.TRIANGLE_STRIP)

        self.ctx.disable(moderngl.BLEND)

    def render_pygame(self, time: float):
        """Render to offscreen surface and copy result into moderngl texture"""
        self.main_surface.fill((0, 0, 0, 0))
        self.foliage_surface.fill((0, 0, 0, 0))

        pygame.draw.rect(self.main_surface,(32,30,48,255),(0,(tile_size[1]*-2-camera_height_coef),1000,100),0)

        # Transform entities and whatever
        self.world.camera.apply_to_group(self.world.entity_list)

        self.world.camera.apply_to_group(self.world.ground.terrain)
        self.world.camera.apply_to_group(self.world.ground.under_terrain)
        self.world.camera.apply_to_group(self.world.ground.foliage)
        for i in self.world.ground.combination_foliage:
            self.world.camera.apply_to_group(i.parts)
        self.world.camera.apply_to_group(self.world.structures.structure_list)

        self.world.camera.apply_to_parallax_group(self.world.background.parallax_layer_6,6)
        self.world.camera.apply_to_parallax_group(self.world.background.parallax_layer_5,5)
        self.world.camera.apply_to_parallax_group(self.world.background.parallax_layer_4,4)
        self.world.camera.apply_to_parallax_group(self.world.background.parallax_layer_3,3)
        self.world.camera.apply_to_parallax_group(self.world.background.parallax_layer_2,2)

        self.world.camera.apply_to_parallax_group(self.world.background.weather_layer_4,4,True)
        self.world.camera.apply_to_parallax_group(self.world.background.weather_layer_5,5,True)
        self.world.camera.apply_to_parallax_group(self.world.background.weather_layer_6,6,True)

        # Draw entities and tiles
        self.world.background.weather_layer_6.draw(self.main_surface)
        self.world.background.parallax_layer_6.draw(self.main_surface)
        self.world.background.parallax_layer_5.draw(self.main_surface)
        self.world.background.parallax_layer_4.draw(self.main_surface)
        self.world.background.parallax_layer_3.draw(self.main_surface)
        self.world.background.parallax_layer_2.draw(self.main_surface)

        self.world.background.weather_layer_5.draw(self.main_surface)
        self.world.background.weather_layer_4.draw(self.main_surface)
    
        self.world.ground.terrain.draw      (self.main_surface)
        self.world.ground.under_terrain.draw(self.main_surface)

        for i in self.world.ground.combination_foliage:
            i.parts.draw(self.foliage_surface)
        
        self.world.ground.foliage.draw      (self.foliage_surface)
        self.world.entity_list.draw         (self.main_surface)

        self.world.structures.structure_list.draw(self.main_surface)

        sky_data = self.sky_surface.get_view("1")
        self.sky_texture.write(sky_data)
        
        foliage_data = self.foliage_surface.get_view("1")
        self.foliage_texture.write(foliage_data)

        texture_data = self.main_surface.get_view("1")
        self.main_texture.write(texture_data)


def main():
    moderngl_window.run_window_config(Pygame, args=("--window", "pygame2"))

if __name__ == "__main__":
    main()
    