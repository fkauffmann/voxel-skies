import math
import numpy as np
import pygame as pg
import time
from settings import *

class Player:
    def __init__(self):
        self.pos = np.array([(MAP_SIZE*NUM_TILES/2), MAP_SIZE*NUM_TILES/2], dtype=float)
        self.angle = -math.pi/2
        self.height = 250
        self.pitch = 0
        self.angle_vel = 0.02
        self.speed = 0
        self.vertical_velocity = 2
        self.pitch_velocity = 4
        self.lateral_velocity = 2
        self.roll = 0
        sheet = pg.image.load("img/player.png")
        self.images = []
        for y in range(0, 256*3, 256):
            for x in range(0, 256*4, 256):
                rect = pg.Rect((x, y, 256, 256))
                image = pg.Surface(rect.size, pg.SRCALPHA, 32)
                image.convert_alpha()
                image.blit(sheet, (0, 0), rect)
                self.images.append(image)

        self.image = self.images[0]
        self.index = 0
        self.ground_elevation = 0 
        self.height_map = np.zeros((1024, 1024, 3))
        self.oscillation = 0
        self.fuel = MAX_FUEL
        self.damages = MAX_DAMAGES
        self.nvg = False
        self.landing_area_pos = (0,0)
        self.landing_area_dist = 0
        self.landed = False

    # return the current heading in degrees (3 digits)
    def get_heading(self):
        radian = self.angle
        degree = math.degrees(radian)
        degree = degree + 90
        if degree>360:
            degree = degree - 360
        if degree<0:
            degree = degree + 360
        return f"{int(degree):03d}"

    # return the current pitch in degrees (3 digits)
    def get_pitch(self):
        degree = self.pitch*90/MAP_SIZE
        return f"{int(degree):03d}"
    
    # return the radar altitude
    def get_radar_altitude(self):
        ralt = self.height - self.ground_elevation - OBJECT_SIZE
        return f"R {int(ralt):03d}" 

    # check if the helicopter collides with the ground
    def is_damaged(self):
        ralt = self.height - self.ground_elevation - OBJECT_SIZE       
        speed = abs(self.speed*100/15)
        roll = abs(self.roll)

        if ralt <= 0 and (roll > 5 or speed > 5):
            if self.damages>0:
                self.damages -= 1
            return True
        else:
            return False
    
    # return the current speed in % (3 digits)
    def get_speed(self):
        speed = self.speed*100/15
        return f"{int(speed*3):03d}"

    # get the current altitude
    def get_altitude(self):
        return f"{int(self.height):05d}"     

    def update(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)

        # handle key presses
        pressed_key = pg.key.get_pressed()
        if pressed_key[pg.K_DOWN]:
            if self.pitch<MAP_SIZE/6:
                self.pitch += self.pitch_velocity
        if pressed_key[pg.K_UP]:
            if self.pitch>-MAP_SIZE/6:
                self.pitch -= self.pitch_velocity

        if pressed_key[pg.K_LEFT]:
            self.roll -= self.angle_vel*50.0
        if pressed_key[pg.K_RIGHT]:
            self.roll += self.angle_vel*50.0

        if self.roll > 45:
            self.roll = 45
        if self.roll < -45:
            self.roll = -45

        if pressed_key[pg.K_w]:
            self.height += self.vertical_velocity 
        if pressed_key[pg.K_s]:
            self.height -= self.vertical_velocity

        if pressed_key[pg.K_a]:
            self.pos[0] += self.lateral_velocity * sin_a
            self.pos[1] -= self.lateral_velocity * cos_a
        if pressed_key[pg.K_d]:
            self.pos[0] -= self.lateral_velocity * sin_a
            self.pos[1] += self.lateral_velocity * cos_a

        # check map boundaries and relocate the player on the center of the map
        if self.pos[0] < MAP_SIZE*2:
            self.pos[0] = (MAP_SIZE * NUM_TILES / 2) - (MAP_SIZE / 2)
        if self.pos[0] > MAP_SIZE * (NUM_TILES - 2):
            self.pos[0] = (MAP_SIZE * NUM_TILES / 2) + (MAP_SIZE / 2)
        if self.pos[1] < MAP_SIZE*2:
            self.pos[1] = (MAP_SIZE * NUM_TILES / 2) - (MAP_SIZE / 2)
        if self.pos[1] > MAP_SIZE * (NUM_TILES - 2):
            self.pos[1] = (MAP_SIZE * NUM_TILES / 2) + (MAP_SIZE / 2)

        # compute the distance of the landing zone
        x1, y1 = self.pos
        x2, y2 = self.landing_area_pos
        self.landing_area_dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        # check if landed
        if self.landing_area_dist<100 and (self.height - self.ground_elevation - OBJECT_SIZE)==0 and self.speed==0:
            self.landed = True
        else:
            self.landed = False

        # increase / decrease speed
        self.speed = -self.pitch*MAX_SPEED/MAP_SIZE*2

        # increase / decrease roll angle
        self.angle += self.angle_vel*self.roll/40

        # check speed limits
        if self.speed < MIN_SPEED:
            self.speed = MIN_SPEED
        if self.speed > MAX_SPEED:
            self.speed = MAX_SPEED

        # change the helicopter position
        self.pos[0] += self.speed * cos_a
        self.pos[1] += self.speed * sin_a            

        # compute the ground elevation below the helicopter
        rel_x = int(self.pos[0] % 1024)
        rel_y = int(self.pos[1] % 1024)
        self.ground_elevation = int(self.height_map[rel_x][rel_y][0])

        # check ground collision
        if self.height < self.ground_elevation + OBJECT_SIZE:
            self.height = self.ground_elevation + OBJECT_SIZE

        # animate the sprite of the helicopter
        self.index = self.index + 1
        if self.index > 3:
            self.index = 0
        if self.pitch<-100:
            self.image = self.images[self.index+4]
        elif self.pitch>100:
            self.image = self.images[self.index+8]
        else:
            self.image = self.images[self.index]

        # add hovering effect
        t = time.time()
        oscillation = (math.sin(t)+1)/2
        self.oscillation = (oscillation * 10) - 5

        # compute fuel consumption
        if self.fuel>0:
            self.fuel -= 1