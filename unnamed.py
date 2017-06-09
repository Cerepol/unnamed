import tdl
import colours
from random import randint

SCREEN_WIDTH= 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 80
MAP_HEIGHT = 45
LIMIT_FPS = 60
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3
FOV_ALGO = 'BASIC'
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 6

colour_light_wall = (150, 150, 100)
colour_dark_wall = (0, 0, 100)
colour_light_ground = (200, 200, 150)
colour_dark_ground = (50, 50, 150)


class Rect:
	def __init__(self, x, y, w, h):
			self.x1 = x
			self.y1 = y
			self.x2 = x + w
			self.y2 = y + h

	def center(self):
		center_x = (self.x1 + self.x2) // 2
		center_y = (self.y1 + self.y2) // 2
		return (center_x, center_y)

	def intersect(self, other):
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
				self.y1 <= other.y2 and self.y2 >= other.y1)

class Tile:
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked
		self.explored = False

		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight

class Fighter:

	def __init__(self, hp, defense, power):
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power

class BasicMonster:
	def take_turn(self):
		print('The ' + self.owner.name + ' growls!')


class GameObject:

	def __init__(self, x, y, char, name, colour, blocks=False, fighter=None, ai=None):
		self.name = name
		self.blocks = blocks
		self.x = x
		self.y = y
		self.char = char
		self.colour = colour

		self.fighter = fighter
		self.ai = ai
		if self.ai:
			self.ai.owner = self

	def move(self, dx, dy):
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy

	def draw(self):
		if (self.x, self.y) in visible_tiles:
			con.draw_char(self.x, self.y, self.char, self.colour, bg=None)

	def clear(self):
		con.draw_char(self.x, self.y, ' ', self.colour, bg=None)

def create_h_tunnel(x1, x2, y):
	global my_map
	for x in range(min(x1, x2), max(x1, x2) + 1):
		my_map[x][y].blocked = False
		my_map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
	global my_map
	for y in range(min(y1, y2), max(y1, y2) + 1):
		my_map[x][y].blocked = False
		my_map[x][y].block_sight = False

def is_visible_tile(x, y):
    global my_map
 
    if x >= MAP_WIDTH or x < 0:
        return False
    elif y >= MAP_HEIGHT or y < 0:
        return False
    elif my_map[x][y].blocked == True:
        return False
    elif my_map[x][y].block_sight == True:
        return False
    else:
        return True

def is_blocked(x, y):
	if my_map[x][y].blocked:
		return True

	for obj in objects:
		if obj.blocks and obj.x == x and obj.y == y:
			return True

	return False

def create_room(room):
		global my_map
		for x in range(room.x1 + 1, room.x2):
			for y in range(room.y1 + 1, room.y2):
				my_map[x][y].blocked = False
				my_map[x][y].block_sight = False

def place_objects(room):
	num_monsters = randint(0, MAX_ROOM_MONSTERS)

	for i in range(num_monsters):
		x = randint(room.x1, room.x2)
		y = randint(room.y1, room.y2)

		if not is_blocked(x, y):
			if randint(0, 100) < 80:
				monster = GameObject(x, y, 'o', 'Orc', colours.desaturated_green, blocks=True)
			else:
				monster = GameObject(x, y, 'T', 'Troll', colours.darker_green, blocks=True)

			objects.append(monster)

def make_map():
	global my_map

	my_map = [[ Tile(True)
		for y in range(MAP_HEIGHT) ]
			for x in range(MAP_WIDTH)]

	rooms = []
	num_rooms = 0

	for r in range(MAX_ROOMS):
		w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		x = randint(0, MAP_WIDTH - w - 1)
		y = randint(0, MAP_HEIGHT - h - 1)

		new_room =  Rect(x, y, w, h)
		failed = False
		for other_room in rooms:
			if new_room.intersect(other_room):
				failed = True
				break

		if not failed:
			create_room(new_room)

			(new_x, new_y) = new_room.center()

			if num_rooms == 0:
				player.x = new_x
				player.y = new_y

			else:
				(prev_x, prev_y) = rooms[num_rooms - 1].center()

				if randint(0, 1):
					create_h_tunnel(prev_x, new_x, prev_y)
					create_v_tunnel(prev_y, new_y, new_x)
				else:
					create_v_tunnel(prev_y, new_y, prev_x)
					create_h_tunnel(prev_x, new_x, new_y)
			
			place_objects(new_room)

			rooms.append(new_room)
			num_rooms += 1

def player_move_or_attack(dx, dy):
	global fov_recompute
	global game_state

	game_state = 'playing'

	x = player.x + dx
	y = player.y + dy

	target = None
	for obj in objects:
		if obj.x == x and obj.y == y:
			target = obj
			break

	if target is not None:
		print('The ' + target.name + ' laughs at your puny efforts at attack him!')
	else:
		player.move(dx, dy)
		fov_recompute = True

def render_all():
	global fov_recompute
	global visible_tiles

	if fov_recompute:
		fov_recompute = False
		visible_tiles = tdl.map.quickFOV(player.x, player.y, is_visible_tile, 
										fov = FOV_ALGO,
										radius = TORCH_RADIUS,
										lightWalls = FOV_LIGHT_WALLS)

		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				visible = (x, y) in visible_tiles
				wall = my_map[x][y].block_sight
				if not visible:
					if my_map[x][y].explored:
						if wall:
							con.draw_char(x,y,None,fg=None,bg=colour_dark_wall)
						else:
							con.draw_char(x,y,'.',fg=None,bg=colour_dark_ground)
				else:
					if wall:
						con.draw_char(x, y, None, fg=None, bg=colour_light_wall)
					else:
						con.draw_char(x, y, ' ', fg=None, bg=colour_light_ground)
					my_map[x][y].explored = True


	for obj in objects:
		obj.draw()

	root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)

#Key Handler
def handle_keys():
	global fov_recompute
	global game_state
	#old
	#key = tdl.event.key_wait()
	#RealTime
	keypress = False
	for event in tdl.event.get():
		if event.type == 'KEYDOWN':
			key = event
			keypress = True
	if not keypress:
		return

	if key.key == '?':
		return 'Help'

	if key.key == 'ESCAPE':
		return 'exit'

	#print(key.keychar)
	#print(key.text)

	if game_state == 'playing':
	#PlayerMovement
		fov_recompute = True
		if key.text == 'j' or key.key == 'KP8':
			player_move_or_attack(0, -1)
		elif key.text == 'k' or key.key == 'KP2':
			player_move_or_attack(0, 1)
		elif key.text == 'h' or key.key == 'KP4':
			player_move_or_attack(-1, 0)
		elif key.text == 'l' or key.key == 'KP6':
			player_move_or_attack(1, 0)
		elif key.text == 'y' or key.key == 'KP7':
			player_move_or_attack(-1, -1)
		elif key.text == 'u' or key.key == 'KP9':
			player_move_or_attack(1, -1)
		elif key.text == 'b' or key.key == 'KP1':
			player_move_or_attack(-1, 1)
		elif key.text == 'n' or key.key == 'KP3':
			player_move_or_attack(1, 1)
		else:
			return 'no-turn'

#===========================================================#
# Init and Main loop
#===========================================================#
tdl.set_font('terminal12x12_gs_ro.png', greyscale=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title='Unnamed Roguelike', fullscreen=False)
tdl.setFPS(LIMIT_FPS)

#main blit console
con = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)

game_state = 'playing'
player_action = None

player = GameObject(0, 0, 1, 'player', (255,255,255), blocks=True)
objects = [player]

make_map()
fov_recompute = True

while not tdl.event.is_window_closed():

	#call the rendering to draw everything
	render_all()
	
	
	tdl.flush()


	for obj in objects:
		obj.clear()

	player_action = handle_keys()

	if game_state == 'playing' and player_action != 'no-turn':
		for obj in objects:
			if obj != player:
				print('The ' + obj.name + ' growls!')

	if player_action == 'exit':
		break

