import random

import numpy as np
import scipy
import scipy.ndimage
import tdl
from skimage import draw

# SETTINGS
DEFAULT_MAP_WIDTH = 80
DEFAULT_MAP_HEIGHT = 50
WINDOW_WIDTH = 80
WINDOW_HEIGHT = 50

# Map Drawing Settings
RECT_MIN_WID = 10
RECT_MAX_WID = 18
RECT_MIN_HEI = 10
RECT_MAX_HEI = 18
MAX_ROOMS = 20
MAX_TRIES = 150

# Dungeon Types/names
# Generic rooms-and-corridors underground dungeon level
DTYPE_NORMAL = 1

# Blueprint Characters
BP_NONE = 'x'
BP_WALL = 'w'
BP_FLOOR = 'f'
BP_CORNER = 'c'

# Display Characters
GRAPHIC_WALL = "#"
GRAPHIC_NONE = " "
GRAPHIC_FLOOR = "."

# Room Types
ROOM_FULL_RECT = "full_rect"
ROOM_FULL_ELLIPSE = "full_ellipse"
ROOM_PREFAB = "prefab"
ROOM_L_SHAPED = "l_shaped"
ROOM_DONUT = "donut"

room_choice_list = [
    [ROOM_FULL_RECT, 50],
    [ROOM_FULL_ELLIPSE, 15],
    [ROOM_PREFAB, 10],
    [ROOM_L_SHAPED, 50],
    [ROOM_DONUT, 50]
]


def weighted_choice(choice_list):
    total = sum(weight for choice, weight in choice_list)
    rand_num = random.uniform(0, total)
    running_total = 0
    for choice, weight in choice_list:
        if running_total + weight >= rand_num:
            return choice
        running_total += weight


tdl.set_font("fonts/meiryu_11.png", 16, 16, False, False, False)
main_window = tdl.init(WINDOW_WIDTH, WINDOW_HEIGHT, "From Darkness", False)
main_window.set_colors([255, 255, 255], [0, 0, 0])


class Level:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Initialize the dungeon by filling it with None objects
        self.map_array = np.zeros((self.width, self.height), dtype=object)
        # Initialize blueprint by filling it with CHAR_NONE (at present, 'x')
        # # self.blueprint = np.array([[BP_NONE for x in range(width)] for y in range(height)])
        # Create an empty list of rooms that will be populated as they're generated
        self.bp = Blueprint(width, height, self)
        self.room_list = []

    # Default level constructor/theme
    def construct(self):
        for x in range(self.width):
            for y in range(self.height):
                # If char in blueprint is BP_NONE, build a wall tile
                # bp.a = blueprint array
                if self.bp.a[x, y] == BP_NONE:
                    self.map_array[x, y] = Tile(True)
                elif self.bp.a[x, y] == BP_WALL:
                    self.map_array[x, y] = Tile(True)
                elif self.bp.a[x, y] == BP_FLOOR:
                    self.map_array[x, y] = Tile(False)

    # Generic Dungeon Builder
    def generate(self, dungeon_type=DTYPE_NORMAL):
        tries = 0
        while len(self.room_list) < MAX_ROOMS:
            if tries >= MAX_TRIES:
                print("Maximum tries reached")
                break
            x = random.randint(0, DEFAULT_MAP_WIDTH)
            y = random.randint(0, DEFAULT_MAP_HEIGHT)
            w = random.randint(RECT_MIN_WID, RECT_MAX_WID)
            h = random.randint(RECT_MIN_HEI, RECT_MAX_HEI)
            shape = weighted_choice(room_choice_list)
            if not self.bp.add_room(x, y, w, h, shape):
                tries += 1
        self.construct()

    def draw(self):
        for x in range(DEFAULT_MAP_WIDTH):
            for y in range(DEFAULT_MAP_HEIGHT):
                if self.map_array[x][y].blocked:
                    main_window.draw_char(x, y, GRAPHIC_WALL)
                else:
                    main_window.draw_char(x, y, GRAPHIC_FLOOR)

    def draw_bp(self):
        for x in range(DEFAULT_MAP_WIDTH):
            for y in range(DEFAULT_MAP_HEIGHT):
                main_window.draw_char(x, y, self.bp.a[x][y])


class Blueprint:
    def __init__(self, w, h, level):
        self.width = w
        self.height = h
        # The Level object that this is linked to
        self.level = level
        # Create a width(w) x height(h) array of BP_NONE to initialize
        self.a = np.array([[BP_NONE for y in range(self.height)] for x in range(self.width)])

    # This attempts to add a room to the blueprint
    # Returns True if successfully added
    def add_room(self, x, y, w, h, shape=ROOM_FULL_RECT):
        room = Room(x, y, w, h)
        room.design(shape)
        if room.collision_check(self):
            return False
        else:
            self.level.room_list.append(room)
            room.add_to_blueprint(self)
            return True


class Room:
    # This is where room masks are stored.
    # Drawing operations done to room masks before being added to the main blueprint and room list
    # are done here.

    def __init__(self, x, y, w, h):
        # X, Y coordinates of top left corner of room.
        # W, H of mask that the room will be contained in
        # Note that a 9x9 "room" is really a 9x9 mask that can hold a 7x7 room at most
        # due to the floor tiles being surrounded by wall tiles.
        # First we make sure the the room won't extend off of the map
        if x + w + 1 > DEFAULT_MAP_WIDTH:
            self.abs_x = DEFAULT_MAP_WIDTH - w - 1
        else:
            self.abs_x = x
        if y + h + 1 > DEFAULT_MAP_HEIGHT:
            self.abs_y = DEFAULT_MAP_HEIGHT - h - 1
        else:
            self.abs_y = y
        self.width = w
        self.height = h
        self.plan = np.array([[BP_NONE for y in range(self.height)] for x in range(self.width)])

    # Rectangle implementation using skimage.draw
    def draw_rect(self, x, y, w, h, char=BP_FLOOR):
        r = np.array([x, x + w - 1, x + w - 1, x, x])
        c = np.array([y, y, y + h - 1, y + h - 1, y])
        rr, cc = draw.polygon(r, c)
        self.plan[rr, cc] = char

    def draw_ellipse(self, wid, hei, x0, y0, a, b):
        for x in range(wid):
            for y in range(hei):
                if ((x - x0) / a) ** 2 + ((y - y0) / b) ** 2 <= .9999999999:
                    self.plan[x][y] = BP_FLOOR

    def design(self, shape):
        # Method that will take the blank room mask and output a room of type "shape"
        if shape == ROOM_FULL_RECT:
            self.draw_rect(1, 1, self.width - 1, self.height - 1)
            self.add_walls()
        elif shape == ROOM_FULL_ELLIPSE:
            wid = self.width - 2
            hei = self.height - 2
            x0 = np.math.floor(wid / 2)  # X Center
            y0 = np.math.floor(hei / 2)  # Y center
            a = x0  # Half Width
            b = y0  # Half Height
            self.draw_ellipse(wid, hei, x0, y0, a, b)
            self.add_walls()
        elif shape == ROOM_PREFAB:
            self.load_room("room.txt")
        elif shape == ROOM_L_SHAPED:
            self.draw_rect(1, 1, self.width - 1, self.height - 1)

            sub_width = random.randint(5, np.math.floor(self.width / 2))
            sub_height = random.randint(5, np.math.floor(self.height / 2))

            self.draw_rect(1, 1, sub_width + 1, sub_height + 1, char=BP_NONE)
            self.random_orientation()
            self.add_walls()
        elif shape == ROOM_DONUT:
            self.draw_rect(1, 1, self.width - 1, self.height - 1)

            sub_width = random.randint(min([4, self.width - 3]), max([4, self.width - 3]))
            sub_height = random.randint(min([4, self.height - 3]), max([4, self.height - 3]))

            sub_x = random.randint(min([4, self.width - sub_width - 2]), max([4, self.width - sub_width - 2]))
            sub_y = random.randint(min([4, self.height - sub_height - 2]), max([4, self.height - sub_height - 2]))

            self.draw_rect(sub_x, sub_y, sub_width - 1, sub_height - 1, char=BP_NONE)
            self.random_orientation()
            self.add_walls()

    def load_room(self, file):
        f = open(file)
        line = f.readline().strip().split()
        x = int(line[0])
        y = int(line[1])
        self.width = y
        self.height = x
        if self.abs_x + self.width + 1 > DEFAULT_MAP_WIDTH:
            self.abs_x = DEFAULT_MAP_WIDTH - self.width - 1
        if self.abs_y + self.height + 1 > DEFAULT_MAP_HEIGHT:
            self.abs_y = DEFAULT_MAP_HEIGHT - self.height - 1
        self.plan = np.array([[BP_NONE for y in range(self.height)] for x in range(self.width)])
        for newline in range(self.width):
            text = f.readline().strip()
            self.plan[newline] = list(text)
        self.random_orientation()

        # if random.randint(0,10) <= 3:
        #     self.plan = np.fliplr(self.plan)
        # if random.randint(0,10) <= 3:
        #     self.plan = np.flipud(self.plan)

    def random_orientation(self):
        orient_choice = random.randint(1, 4)
        if orient_choice == 2:
            self.plan = np.flipud(self.plan)
        elif orient_choice == 3:
            self.plan = np.fliplr(self.plan)
        elif orient_choice == 4:
            self.plan = np.flipud(self.plan)
            self.plan = np.fliplr(self.plan)

    def add_walls(self):
        # A function that takes an array of BP_FLOOR and BP_NONE tiles and adds BP_WALL touching all BP_FLOOR
        #
        # Array of the same size as floor mask where True are BP_FLOOR tiles
        floor_mask = self.plan == BP_FLOOR
        # Create the structure to use for the dilation function
        dilation_struct = scipy.ndimage.generate_binary_structure(2, 2)
        # Array of same size as floor mask where True are BP_WALL tiles
        wall_mask = scipy.ndimage.binary_dilation(floor_mask, dilation_struct)
        for x in range(self.width):
            for y in range(self.height):
                # Checking if there is a wall but not a floor there
                if wall_mask[x][y] and not floor_mask[x][y]:
                    self.plan[x][y] = BP_WALL

    # Checks for a collision on blueprint. Returns True if there is a collision
    def collision_check(self, blueprint):
        for x in range(self.width):
            for y in range(self.height):
                if self.plan[x][y] == BP_FLOOR:
                    check_tile = blueprint.a[x + self.abs_x][y + self.abs_y]
                    if check_tile == BP_WALL or check_tile == BP_FLOOR:
                        return True

    def add_to_blueprint(self, blueprint):
        for x in range(self.width):
            for y in range(self.height):
                if self.plan[x][y] == BP_FLOOR or self.plan[x][y] == BP_WALL:
                    blueprint.a[x + self.abs_x][y + self.abs_y] = self.plan[x][y]


class Tile:
    def __init__(self, blocked, blocks_vision=None):
        self.blocked = blocked
        self.blocks_vision = blocked if blocks_vision is None else blocks_vision


testbed = Level(DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT)
testbed.generate()
# testbed.draw_bp()
testbed.draw()

while not tdl.event.is_window_closed():
    tdl.flush()
