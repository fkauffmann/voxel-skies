import pygame as pg
import sys
from player import Player
from explosion import Explosion
from voxel_render import VoxelRender

class App:
    def __init__(self):
        pg.init()
        pg.mixer.init()        
        self.fullscreen = False
        self.res = self.width, self.height = (640, 360)
        self.screen = pg.display.set_mode(self.res)
        self.clock = pg.time.Clock()
        self.player = Player()
        self.explosion = Explosion()
        self.voxel_render = VoxelRender(self)

        # play helicopter sound in background
        if pg.mixer.get_init():
            pg.mixer.music.load("sounds/helicopter.wav")
            pg.mixer.music.set_volume(0.8)
            pg.mixer.music.play(-1)        

    def update(self):
        self.player.update()
        self.explosion.update()
        self.voxel_render.update()

    def draw(self):
        self.voxel_render.draw()
        pg.display.flip()

    def run(self):
        while True:
            self.update()
            self.draw()

            for event in pg.event.get():
                if event.type == pg.QUIT or (
                        event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    sys.exit()
                if event.type == pg.KEYDOWN and event.key == pg.K_l:
                    self.voxel_render.change_map()
                if event.type == pg.KEYDOWN and event.key == pg.K_F11:
                    if self.fullscreen:
                        self.screen = pg.display.set_mode(self.res)
                    else:
                        self.screen = pg.display.set_mode(self.res, pg.SCALED | pg.FULLSCREEN)
                    self.fullscreen = not self.fullscreen

            #pg.mixer.music.set_volume(0.4 + (abs(self.player.speed)/7))

            self.clock.tick(60)
            pg.display.set_caption(f'FPS: {int(self.clock.get_fps())} - [F11]: Fullscreen')

if __name__ == '__main__':
    app = App()
    app.run()
