import pygame as pg
import sys
from player import Player
from explosion import Explosion
from voxel_render import VoxelRender

###############################################################################
# VOXEL SKIES
# A small helicopter simulator heavily inspired by Comanche: Maximum Overkill, 
# published in 1992 by Novalogic.
###############################################################################

class App:
    def __init__(self):
        pg.init()
        pg.mixer.init()        

        self.res = self.width, self.height = (640, 360)
        self.screen = pg.display.set_mode(self.res, pg.SCALED | pg.RESIZABLE)
        pg.display.set_icon(pg.image.load('img/icon.png'))
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
                # quit game
                if event.type == pg.QUIT or (
                        event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    sys.exit()
                # load next map
                if event.type == pg.KEYDOWN and event.key == pg.K_l:
                    self.voxel_render.change_map()
                # toggle night vision goggles
                if event.type == pg.KEYDOWN and event.key == pg.K_n:
                    self.player.nvg = not self.player.nvg

            self.clock.tick(60)
            pg.display.set_caption(f'FPS: {int(self.clock.get_fps())}')

if __name__ == '__main__':
    app = App()
    app.run()
