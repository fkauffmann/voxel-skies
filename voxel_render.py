import math
from numba import njit
import random
import numpy as np
import pygame as pg

HUD_COLOR = (0, 255, 150)
BG_DARK = (0, 0, 0, 50)
BG_SELECTION = (0, 255, 255, 80)
MAX_FUEL = 5000
MAX_DAMAGE = 100
NUM_TILES = 9
NUM_MAPS = 10

@njit(fastmath=True)    
def repeat_tiles(height_map, map_size):
    # Get the current dimensions of the original image
    height, width = height_map.shape[:2]

    # Create a new larger array with map_size times the height and width
    new_height = height * map_size
    new_width = width * map_size
    new_height_map = np.zeros((new_height, new_width, 3), dtype=height_map.dtype)

    # Calculate offsets to center the original image in the expanded array
    y_offset = height
    x_offset = width

    for y in range(0,map_size):
        for x in range(0,map_size):
            new_height_map[y*y_offset:(y+1)*y_offset, x*x_offset:(x+1)*x_offset] = height_map

    return new_height_map

def load_map(path):
    img = pg.image.load(path)
    return repeat_tiles(pg.surfarray.array3d(img), 10)

def extract_minimap(color_map, x, y):
    # convert parameters to integers
    x = int(x)
    y = int(y)
    
    # size of the map to be extracted
    size = 512
    
    # compute the area to be extracted while ensuring we stay within bounds
    x_start = max(0, x - size)
    x_end = min(color_map.shape[0], x + size)
    y_start = max(0, y - size)
    y_end = min(color_map.shape[1], y + size)

    # extract the color map
    cropped_map = color_map[x_start:x_end, y_start:y_end, :]
      
    # create a pygame surface from a RGB array
    surface = pg.surfarray.make_surface(cropped_map)
    
    return surface

@njit(fastmath=True)
def ray_casting(screen_array, player_pos, player_angle, player_height, player_pitch,
                     screen_width, screen_height, delta_angle, ray_distance, h_fov, scale_height, 
                     color_map, height_map, sky_texture, scroll_x, nvg):

    map_height = len(height_map[0])
    map_width = len(height_map)

    if not nvg:
        # width of the sky image
        width_sky = sky_texture.shape[0]

        # if the offset exceeds the width of the image, reset it to loop
        scroll_x %= width_sky
        remaining_width = width_sky - scroll_x

        # if the visible part does not go beyond the end of the image
        if remaining_width >= screen_array.shape[0]:
            screen_array[:, :] = sky_texture[scroll_x:scroll_x + screen_array.shape[0], :screen_array.shape[1]]
        else:
            # if the visible part exceeds the image's end, we split it into two parts           
            screen_array[:remaining_width, :] = sky_texture[scroll_x:, :screen_array.shape[1]]
            screen_array[remaining_width:, :] = sky_texture[:screen_array.shape[0] - remaining_width, :screen_array.shape[1]]
    else:
        # dark sky (NVG mode)
        screen_array[:] = 0

    y_buffer = np.full(screen_width, screen_height)

    ray_angle = player_angle - h_fov
    for num_ray in range(screen_width):
        first_contact = False
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        # NVG optimization: pre-calculate the NVG color (constant for this ray)
        nvg_color = np.array([0.0, 0.0, 0.0]) if nvg else None

        for depth in range(1, ray_distance):
            x = int(player_pos[0] + depth * cos_a)
            if 0 < x < map_width:
                y = int(player_pos[1] + depth * sin_a)
                if 0 < y < map_height:

                    # remove fish eye and get height on screen
                    depth *= math.cos(player_angle - ray_angle)
                    height_on_screen = int((player_height - height_map[x, y][0]) /
                                           depth * scale_height + player_pitch)

                    # remove unnecessary drawing
                    if not first_contact:
                        y_buffer[num_ray] = min(height_on_screen, screen_height)
                        first_contact = True
                    # remove mirror bug
                    if height_on_screen < 0:
                        height_on_screen = 0

                    # draw vert line
                    if height_on_screen < y_buffer[num_ray]:
                        if nvg:
                            for screen_y in range(height_on_screen, y_buffer[num_ray]):
                                # Set NVG color directly
                                screen_array[num_ray, screen_y] = [0.0, max(0,color_map[x, y][1]-random.randint(0,30)), 0.0]
                        else:
                            object_color = color_map[x, y]
                            for screen_y in range(height_on_screen, y_buffer[num_ray]):
                                screen_array[num_ray, screen_y] = object_color

                        y_buffer[num_ray] = height_on_screen

        ray_angle += delta_angle
    return screen_array


def draw_rect_alpha(surface, color, rect):
    shape_surf = pg.Surface(pg.Rect(rect).size, pg.SRCALPHA)
    pg.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)

def draw_circle_alpha(surface, color, center, radius):
    target_rect = pg.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
    shape_surf = pg.Surface(target_rect.size, pg.SRCALPHA)
    pg.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_rect)

def draw_polygon_alpha(surface, color, points):
    lx, ly = zip(*points)
    min_x, min_y, max_x, max_y = min(lx), min(ly), max(lx), max(ly)
    target_rect = pg.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    shape_surf = pg.Surface(target_rect.size, pg.SRCALPHA)
    pg.draw.polygon(shape_surf, color, [(x - min_x, y - min_y) for x, y in points])
    surface.blit(shape_surf, target_rect)

def project_point(origin_x, origin_y, distance, angle_rad):
    # compute the x, y position of the end of the line 
    end_x = origin_x + distance * math.cos(angle_rad)
    end_y = origin_y - distance * math.sin(angle_rad)  # Moins car l'axe y de Pygame est inversé
    return end_x, end_y

def draw_dashed_line(screen, color, start_pos, end_pos, width=1, dash_length=10):
    x1, y1 = start_pos
    x2, y2 = end_pos
    dl = dash_length

    if (x1 == x2):
        ycoords = [y for y in range(y1, y2, dl if y1 < y2 else -dl)]
        xcoords = [x1] * len(ycoords)
    elif (y1 == y2):
        xcoords = [x for x in range(x1, x2, dl if x1 < x2 else -dl)]
        ycoords = [y1] * len(xcoords)
    else:
        a = abs(x2 - x1)
        b = abs(y2 - y1)
        c = round(math.sqrt(a**2 + b**2))
        dx = dl * a / c
        dy = dl * b / c

        xcoords = [x for x in np.arange(x1, x2, dx if x1 < x2 else -dx)]
        ycoords = [y for y in np.arange(y1, y2, dy if y1 < y2 else -dy)]

    next_coords = list(zip(xcoords[1::2], ycoords[1::2]))
    last_coords = list(zip(xcoords[0::2], ycoords[0::2]))
    for (x1, y1), (x2, y2) in zip(next_coords, last_coords):
        start = (round(x1), round(y1))
        end = (round(x2), round(y2))
        pg.draw.line(screen, color, start, end, width)


def draw_rotated_line(screen, startx, starty, endx, endy, centerx, centery, angle, color, thickness, is_dashed):
    # Convert angle from degrees to radians
    angle_rad = math.radians(angle)

    # Function to rotate a point around the center
    def rotate_point(px, py, cx, cy, angle_rad):
        # Translate point to origin
        translated_x = px - cx
        translated_y = py - cy
        
        # Apply rotation
        rotated_x = translated_x * math.cos(angle_rad) - translated_y * math.sin(angle_rad)
        rotated_y = translated_x * math.sin(angle_rad) + translated_y * math.cos(angle_rad)
        
        # Translate point back
        return int(rotated_x + cx), int(rotated_y + cy)

    # Rotate the start and end points around the center
    rotated_startx, rotated_starty = rotate_point(startx, starty, centerx, centery, angle_rad)
    rotated_endx, rotated_endy = rotate_point(endx, endy, centerx, centery, angle_rad)

    # Draw the line with the rotated coordinates
    if is_dashed:
        draw_dashed_line(screen, color, (rotated_startx, rotated_starty), (rotated_endx, rotated_endy), thickness, 5)
    else:
        pg.draw.line(screen, color, (rotated_startx, rotated_starty), (rotated_endx, rotated_endy), thickness)


class VoxelRender:
    def __init__(self, app):
        self.app = app
        self.player = app.player
        self.explosion = app.explosion
        self.fov = math.pi / 4
        self.h_fov = self.fov / 4
        self.num_rays = app.width
        self.delta_angle = self.fov / self.num_rays
        self.ray_distance = 1800
        self.scale_height = 340
        self.screen_array = np.full((app.width, app.height, 3), (0, 0, 0))
        self.hud_font_small = pg.freetype.Font("./fonts/lcd.ttf", 16)
        self.map_id = 0
        self.height_map = load_map('img/map'+str(self.map_id)+'_height.png')
        self.color_map = load_map('img/map'+str(self.map_id)+'_color.png')
        self.player.height_map = self.height_map
        self.sky_offset_x = 0
        self.sky = pg.surfarray.array3d(pg.image.load('img/sky.png'))

    def update(self):
        # update the sky location
        self.sky_offset_x += int(self.player.roll/5)

        # ray trace the scenery
        self.screen_array = ray_casting(self.screen_array, self.player.pos, self.player.angle,
                                        self.player.height, self.player.pitch, self.app.width,
                                        self.app.height, self.delta_angle, self.ray_distance,
                                        self.h_fov, self.scale_height, self.color_map, self.height_map, 
                                        self.sky, self.sky_offset_x, self.player.nvg)

    # load the next map
    def change_map(self):
        self.map_id = self.map_id + 1
        if self.map_id >= NUM_MAPS:
            self.map_id = 0
        self.height_map = load_map('img/map'+str(self.map_id)+'_height.png')
        self.color_map = load_map('img/map'+str(self.map_id)+'_color.png')
        self.player.height_map = self.height_map

    # draw main dashboard
    def draw_cockpit(self):
        # draw mini map
        self.app.screen.blit(
            pg.transform.scale(
            extract_minimap(self.color_map, self.player.pos[0], self.player.pos[1]), (64,64)), (11,self.app.height-75))

        # view port
        aperture = math.pi/8
        p0 = (44, self.app.height-76+32)
        p1 = project_point(44, self.app.height-76+32, 32, -self.app.player.angle-aperture)
        p2 = project_point(44, self.app.height-76+32, 32, -self.app.player.angle+aperture)
        draw_polygon_alpha(self.app.screen, BG_SELECTION, [p0, p1, p2])

        # green borders
        pg.draw.rect(self.app.screen, HUD_COLOR, pg.Rect(10, self.app.height-76, 66, 66), 1)

    # draw head-up-display
    def draw_hud(self):
        # top (heading)
        self.hud_font_small.render_to(self.app.screen, (self.app.width/2-12, self.app.height/2-100), 
                                      self.app.player.get_heading(), HUD_COLOR)
        # right (altitudes)
        self.hud_font_small.render_to(self.app.screen, (self.app.width/2+110, self.app.height/2-5), 
                                      self.app.player.get_altitude(), HUD_COLOR)
        if self.player.height<256:
            self.hud_font_small.render_to(self.app.screen, (self.app.width/2+110, self.app.height/2+10), 
                                          self.app.player.get_radar_altitude(), HUD_COLOR)
        # left (velocity)
        self.hud_font_small.render_to(self.app.screen, (self.app.width/2-130, self.app.height/2-5), 
                                      str(self.app.player.get_speed()), HUD_COLOR)

        # artificial horizon 
        for i in range(-300, 360, 60):
            offset_y = self.player.pitch+i
            if i==0:
                pg.draw.line(self.app.screen, HUD_COLOR,
                             (self.app.width / 2 - 90, self.app.height / 2),
                             (self.app.width / 2 - 95, self.app.height / 2 - 5))
                pg.draw.line(self.app.screen, HUD_COLOR,
                             (self.app.width / 2 - 90, self.app.height / 2),
                             (self.app.width / 2 - 95, self.app.height / 2 + 5))
                pg.draw.line(self.app.screen, HUD_COLOR,
                             (self.app.width / 2 + 90, self.app.height / 2),
                             (self.app.width / 2 + 95, self.app.height / 2 - 5))
                pg.draw.line(self.app.screen, HUD_COLOR,
                             (self.app.width / 2 + 90, self.app.height / 2),
                             (self.app.width / 2 + 95, self.app.height / 2 + 5))                                                

                draw_rotated_line(self.app.screen, 
                                self.app.width / 2 - 90, self.app.height / 2 + offset_y,
                                self.app.width / 2 - 30, self.app.height / 2 + offset_y,
                                self.app.width/2, self.app.height/2,
                                -self.player.roll,
                                HUD_COLOR, 1, False
                                )
                draw_rotated_line(self.app.screen, 
                                self.app.width / 2 + 90, self.app.height / 2 + offset_y,
                                self.app.width / 2 + 30, self.app.height / 2 + offset_y,
                                self.app.width/2, self.app.height/2,
                                -self.player.roll,
                                HUD_COLOR, 1, False
                                )
            else:
                draw_rotated_line(self.app.screen, 
                                self.app.width / 2 - 70, self.app.height / 2 + offset_y,
                                self.app.width / 2 - 30, self.app.height / 2 + offset_y,
                                self.app.width/2, self.app.height/2,
                                -self.player.roll,
                                HUD_COLOR, 1, (i>0)
                                )
                draw_rotated_line(self.app.screen, 
                                self.app.width / 2 + 70, self.app.height / 2 + offset_y,
                                self.app.width / 2 + 30, self.app.height / 2 + offset_y,
                                self.app.width/2, self.app.height/2,
                                -self.player.roll,
                                HUD_COLOR, 1, (i>0)
                                )

        # damages
        draw_rect_alpha(self.app.screen, BG_SELECTION, 
                     pg.Rect(self.app.width-110, self.app.height-20, self.player.damages, 10))
        pg.draw.rect(self.app.screen, HUD_COLOR, 
                     pg.Rect(self.app.width-110, self.app.height-20, 100, 10), 1)
        self.hud_font_small.render_to(self.app.screen, (self.app.width-150, self.app.height-20), 
                                      "DMG", HUD_COLOR)

        # fuel qty
        draw_rect_alpha(self.app.screen, BG_SELECTION, 
                     pg.Rect(self.app.width-110, self.app.height-40, self.player.fuel*100/MAX_FUEL, 10))        
        pg.draw.rect(self.app.screen, HUD_COLOR, 
                     pg.Rect(self.app.width-110, self.app.height-40, 100, 10), 1)
        self.hud_font_small.render_to(self.app.screen, (self.app.width-150, self.app.height-40), 
                                      "FUEL", HUD_COLOR)



    def draw_player(self):
        # rotate and scale the sprite
        zoom_factor = 0.75 - (self.player.speed*0.25/7)
        image_rotated_zoomed = pg.transform.rotozoom(self.player.image, -self.player.roll, zoom_factor)
        
        # compute the new size of the sprite
        image_width, image_height = image_rotated_zoomed.get_size()
        
        # draw the sprite at the center of the screen
        self.app.screen.blit(
            image_rotated_zoomed, 
            (self.app.width / 2 - image_width / 2, self.app.height / 2 - image_height / 2 + self.player.oscillation)
        )

    def draw_explosion(self):
        if self.player.is_damaged():
            self.app.screen.blit(self.explosion.image, (self.app.width / 2 - 40, self.app.height / 2 - 32))
    
    # draw components
    def draw(self):
        # draw scenery
        pg.surfarray.blit_array(self.app.screen, self.screen_array)

        # draw dashboard
        self.draw_cockpit()

        # draw hud
        self.draw_hud()

        # draw player
        self.draw_player()

        # draw ground collision
        self.draw_explosion()