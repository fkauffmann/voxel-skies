import pygame as pg
import time
import math
import sys
from player import Player
from explosion import Explosion
from voxel_render import VoxelRender

###############################################################################
# VOXEL SKIES
# A small helicopter simulator heavily inspired by Comanche: Maximum Overkill, 
# published in 1992 by Novalogic.
###############################################################################

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 360
MAX_FUEL = 5000
MAX_DAMAGES = 100

class App:
    def __init__(self):
        pg.init()
        pg.mixer.init()        

        self.res = self.width, self.height = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.screen = pg.display.set_mode(self.res, pg.SCALED | pg.RESIZABLE)
        self.intro = pg.image.load('img/intro.jpg')
        self.large_font = pg.freetype.Font("./fonts/voxel.ttf", 64)
        self.small_font = pg.freetype.Font("./fonts/lcd.ttf", 18)
        self.clock = pg.time.Clock()
        self.player = Player()
        self.explosion = Explosion()
        self.voxel_render = VoxelRender(self)
        self.stage = 0
        self.current_track = 0
        self.previous_track = -1
        
        pg.display.set_icon(pg.image.load('img/icon.png'))

    def update(self):

        self.current_track = self.stage

        # play music in background
        if self.current_track==0 and self.current_track!=self.previous_track:
            if pg.mixer.get_init():
                pg.mixer.music.load("sounds/soundtrack.flac")
                pg.mixer.music.set_volume(0.4)      
                pg.mixer.music.play(-1) 
            self.previous_track = self.current_track

        # play helicopter sound in background
        if self.current_track==1 and self.current_track!=self.previous_track:
            if pg.mixer.get_init():
                pg.mixer.music.load("sounds/helicopter.wav")
                pg.mixer.music.set_volume(0.8)      
                pg.mixer.music.play(-1) 
            self.previous_track = self.current_track

        if self.stage==1:
            self.player.update()
            self.explosion.update()
            self.voxel_render.update()

    def draw(self):
        # intro screen
        if self.stage==0:
            intro_screen = pg.transform.scale(self.intro, (WINDOW_WIDTH, WINDOW_HEIGHT+20))
            t = time.time()
            offset_y = (math.sin(t)+1)*10  
            self.screen.blit(intro_screen, (0, offset_y-20))
            
            self.large_font.render_to(self.screen, (WINDOW_WIDTH/2-235, WINDOW_HEIGHT-150), 
                                      "VOXEL SKIES", (255,255,255))
            self.small_font.render_to(self.screen, (WINDOW_WIDTH/2-90, WINDOW_HEIGHT-70), 
                                      "PRESS SPACE TO CONTINUE", (255,255,255))


        # game screen
        if self.stage==1:
            self.voxel_render.draw()

        # crashed! (restart current level)
        if self.player.damages==0 or self.player.fuel==0:
            self.player.damages = MAX_DAMAGES
            self.player.fuel = MAX_FUEL
            self.stage = 0

        # landed (load next map)
        if self.player.landed:
            self.player.landed = False
            self.voxel_render.change_map()
            self.stage = 0
        
        pg.display.flip()

    def run(self):
        while True:
            self.update()
            self.draw()

            for event in pg.event.get():
                # quit the game
                if event.type == pg.QUIT or (
                        event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    sys.exit()
                if self.stage==0:
                    # skip the intro screen
                    if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                        self.stage = 1
                if self.stage==1:
                    # load next map (debug)
                    if event.type == pg.KEYDOWN and event.key == pg.K_d :
                        self.voxel_render.change_map()
                    # toggle night vision goggles
                    if event.type == pg.KEYDOWN and event.key == pg.K_n:
                        self.player.nvg = not self.player.nvg

            self.clock.tick(60)
            pg.display.set_caption(f'FPS: {int(self.clock.get_fps())}')

if __name__ == '__main__':
    app = App()
    app.run()
