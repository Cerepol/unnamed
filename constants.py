#Screen Constants
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
#LIMIT_FPS = 60

#Map Constants
MAP_WIDTH = 80
MAP_HEIGHT = 43
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2

#Layer Constants
BASE_LAYER = 0
OBJECT_LAYER = 1
EFFECT_LAYER = 2
UI_LAYER = 249
UI_TEXT_LAYER = 250
OVERLAY_LAYER = 240
CURSOR_LAYER = 242
MENU_UNDERLAYER = 254
MENU_LAYER = 255

#Player Constants
FOV_ALGO = 'SHADOW'
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 7

#UI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
#BLOCK_CHAR = '\u2588'
BLOCK_CHAR = chr(219)
BACKTRACK=False

SAVE_PATH = './saves/'

#colour_light_wall = (150, 150, 100)
#colour_dark_wall = (0, 0, 100)
#colour_light_ground = (200, 200, 150)
#colour_dark_ground = (50, 50, 150)