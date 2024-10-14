import pygame as pg

class Explosion:
    def __init__(self):
        self.pos = (0,0)
        sheet = pg.image.load("img/explosion.png") # 1536x96 (16 images)
        self.images = []
        for x in range(0, 1536, 96):
            rect = pg.Rect((x, 0, 96, 96))
            image = pg.Surface(rect.size, pg.SRCALPHA, 32)
            image.convert_alpha()
            image.blit(sheet, (0, 0), rect)
            self.images.append(image)

        self.image = self.images[0]
        self.index = 0

    def update(self):
        # animate the sprite of the explosion
        self.index = self.index + 1
        if self.index > 15:
            self.index = 0
        self.image = self.images[self.index]
