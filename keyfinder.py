from bearlibterminal import terminal as t

#Screen Constants
SCREEN_WIDTH= 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 60

#Map Constants
MAP_WIDTH = 80
MAP_HEIGHT = 43
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2

#Player Constants
FOV_ALGO = 'BASIC'
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 6

#UI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50

colour_light_wall = (150, 150, 100)
colour_dark_wall = (0, 0, 100)
colour_light_ground = (200, 200, 150)
colour_dark_ground = (50, 50, 150)



t.open()
t.set("window: size=80x50, resizeable=true;" +
			 "font: ./terminal12x12_gs_ro.png, size=12x12")

t.refresh()
key = t.read()

if 4 == (3 or 4):
	print("hi")

if 4 ==(3 or 6):
	print("nope")

while key != (t.TK_ESCAPE or t.TK_CLOSE):
	print(key)
	key = t.read()


t.close()