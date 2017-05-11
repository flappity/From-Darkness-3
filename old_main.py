import tdl
import random
import numpy as np
import scipy.ndimage
import scipy

# SETTINGS
MAP_WIDTH = 80
MAP_HEIGHT = 50
WINDOW_WIDTH = 80
WINDOW_HEIGHT = 50

# MAP GENERATION SETTINGS
MASK_MIN_X = 8
MASK_MAX_X = 18
MASK_MIN_Y = 8
MASK_MAX_Y = 18
MAX_ROOMS = 20

tdl.set_font("fonts/meiryu_11.png", 16, 16, False, False, False)
main_window = tdl.init(WINDOW_WIDTH, WINDOW_HEIGHT, "From Darkness", False)
main_window.set_colors([255, 255, 255], [0, 0, 0])


class Tile:
    def __init__(self, blocked, blocks_vision=None, visible=False):
        self.blocked = blocked
        self.blocks_vision = blocked if blocks_vision is None else blocks_vision
        self.visible = visible
        self.char = ""

    def dig(self):
        if self.blocked:
            self.blocked = False
            self.blocks_vision = False

    def fill(self):
        if not self.blocked:
            self.blocked = True
            self.blocks_vision = True

    def status(self):
        return self.blocked

class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.array = np.array([[Tile(True) for x in range(height)] for y in range(width)])
        self.blueprint = np.array([['x' for x in range(height)] for y in range(width)])
        self.rooms = []

    # def draw(self):
    #     for x in range(self.width):
    #         for y in range(self.height):
    #             if self.array[x][y].blocked:
    #                 if self.array[x][y].visible:
    #                     main_window.draw_char(x, y, "#")
    #                 else:
    #                     main_window.draw_char(x, y, "x")
    #             else:
    #                 main_window.draw_char(x, y, ".")

    def build(self):
        for x in range(self.width):
            for y in range(self.height):
                main_window.draw_char(x, y, self.blueprint[x][y])
                # if self.blueprint[x][y] == 'f':
                #     self.array[x][y].blocked = False
                # elif self.blueprint[x][y] == 'w':
                #     self.array[x][y].blocked = True
                #     self.array[x][y].visible = True
                # else:
                #     self.array[x][y].blocked = True
                #     self.array[x][y].visible = False


    # Returns False if the room was not added (due to collision)
    # Returns True if the room was successfully added
    def add_rect_room(self,x,y,w,h):
        newroom = Room(self,x,y,w,h)
        newroom.make_rect()
        #if newroom.check_for_collision():
        #    return False
        self.rooms.append(newroom)
        newroom.draw_room()
        return True

    def add_circular_room(self,x,y,w,h):
        newroom = Room(self,x,y,w,h)
        newroom.make_ellipse()
        #if newroom.check_for_collision():
        #    return False
        self.rooms.append(newroom)
        newroom.draw_room()
        print("Circular room added!")
        return True

    def generate_map(self):
        room_tries = 0
        self.rooms = []
        while len(self.rooms) <= MAX_ROOMS:
            x = random.randint(0,self.width)
            y = random.randint(0,self.height)
            w = random.randint(MASK_MIN_X, MASK_MAX_X)
            h = random.randint(MASK_MIN_Y, MASK_MAX_Y)
            if random.randint(0, 10) < 1 and self.height > 8 and self.width > 8:
                if not self.add_circular_room(x, y, w, h):
                    room_tries += 1
            if not self.add_rect_room(x, y, w, h):
                room_tries += 1
            if room_tries == 5:
                print("Tries Exceeded!")
                break


class Room:
    def __init__(self, containing_map, x, y, mask_w, mask_h):
        # Make sure the room won't extend past the edge of the map that contains it
        self.containing_map = containing_map
        if x + mask_w >= containing_map.width - 1:
            self.origin_x = containing_map.width - mask_w - 1
        else:
            self.origin_x = x
        if y + mask_h >= containing_map.height - 1:
            self.origin_y = containing_map.height - mask_h - 1
        else:
            self.origin_y = y
        self.mask_w = mask_w
        self.mask_h = mask_h
        # Put False in every space in the grid to initialize the mask
        # This will change when we use a draw function to build the type of room we need
        self.mask = np.array([['a'
                     for wy in range(self.mask_h)]
                     for wx in range(self.mask_w)])

    def make_rect(self):
        # self.mask = [["w"
        #             for wy in range(self.mask_h)]
        #             for wx in range(self.mask_w)]
        for x in range(1, self.mask_w - 1):
            for y in range(1, self.mask_h - 1):
                self.mask[x][y] = "f"
        self.add_mask_walls()

    # Makes a rougly octagonal/elliptical room
    def make_ellipse(self):
        #self.mask = [["w"
        #             for wy in range(self.mask_h)]
        #             for wx in range(self.mask_w)]
        # # If width = height,
        # if self.mask_w == self.mask_h:
        #     circle_a = numpy.math.floor(self.mask_w / 2)
        #     circle_b = numpy.math.floor(self.mask_h / 2)
        #     circle_r = min(circle_a, circle_b)
        #     for x in range(self.mask_w):
        #         for y in range(self.mask_h):
        #             if (x - circle_a)**2 + (y - circle_b) ** 2 < circle_r ** 2:
        #                 self.mask[x][y] = "f"
            #(x - a)**2 + (y - b)**2 = r**2
        #else:
        wid = self.mask_w - 1
        hei = self.mask_h - 1
        x0 = np.math.floor(wid / 2)  # X Center
        y0 = np.math.floor(hei / 2)   # Y center
        a = x0   # Half Width
        b = y0   # Half Height
        x = np.linspace(0, self.mask_w, wid*2 - 1)
        y = np.linspace(0, self.mask_h, hei*2 - 1)
        for x in range(self.mask_w):
            for y in range(self.mask_h):
                if ((x-x0)/a)**2 + ((y-y0)/b)**2 <= .9999999999:
                    self.mask[x][y] = "f"
        self.add_mask_walls()
        print(self.mask)




    def add_mask_walls(self):
        # Create a numpy array where floor "f" tiles correspond to True tiles, with all else being False
        floor_mask = np.array(self.mask) == 'f'
        #print(floor_mask)
        # Create dilation structure
        dilation_struct = scipy.ndimage.generate_binary_structure(2,2)

        # Dilate the mask (basically expand it out by one tile
        wall_mask = scipy.ndimage.binary_dilation(floor_mask,dilation_struct)

        # Initialize the final array
        endarray = np.zeros((self.mask_w, self.mask_h), dtype=str)

        # Create a final mask based on the initial + dilated mask
        # Returns a np.array of walls, floors, and 'undug' areas
        for x in range(self.mask_w):
            for y in range(self.mask_h):
                # If dilated = True and original
                if wall_mask[x][y] and not floor_mask[x][y]:
                    self.mask[x][y] = 'w'
                if not wall_mask[x][y]:
                    self.mask[x][y] = 'x'
                if floor_mask[x][y]:
                    self.mask[x][y] = 'f'

        # print("self.mask")
        # print(self.mask)
        # print("endarray")
        # print(endarray)


    def draw_room(self):
        for x in range(self.mask_w):
            for y in range(self.mask_h):
                self.containing_map.blueprint[self.origin_x + x][self.origin_y + y] = self.mask[x][y]

    # Returns True if there is a collision
    def check_for_collision(self):
        for x in range(self.mask_w):
            for y in range(self.mask_h):
                if self.mask[x][y] == "f" or "w":
                    if self.containing_map.blueprint[x][y] == 'w' or 'f':
                        print("Collision Detected")
                        return True








base_dungeon = Map(MAP_WIDTH, MAP_HEIGHT)
base_dungeon.generate_map()
base_dungeon.build()
#base_dungeon.draw()


while not tdl.event.is_window_closed():
    tdl.flush()