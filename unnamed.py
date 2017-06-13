import tdl
import colours
import math
import textwrap
from random import randint

SCREEN_WIDTH= 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 80
MAP_HEIGHT = 43
LIMIT_FPS = 60
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3
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

	def __init__(self, hp, defense, power, death_function=None):
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power
		self.death_function = death_function

	def take_damage(self, damage):
		if damage > 0:
			self.hp -= damage

		if self.hp <= 0:
			function = self.death_function
			if function is not None:
				function(self.owner)

	def attack(self, target):
		damage = self.power - target.fighter.defense

		if damage > 0:
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' damage.', colours.red)
			target.fighter.take_damage(damage)
		else:
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!', colours.light_red)

class BasicMonster:
	def take_turn(self):
		monster = self.owner

		if(monster.x, monster.y) in visible_tiles:
			if monster.distance_to(player) >= 2:
				monster.move_towards(player.x, player.y)
			elif player.fighter.hp > 0:
				monster.fighter.attack(player)


class GameObject:

	def __init__(self, x, y, char, name, colour, blocks=False, fighter=None, ai=None):
		self.name = name
		self.blocks = blocks
		self.x = x
		self.y = y
		self.char = char
		self.colour = colour

		self.fighter = fighter
		if self.fighter:
			self.fighter.owner = self

		self.ai = ai
		if self.ai:
			self.ai.owner = self

	def move(self, dx, dy):
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy

	def move_towards(self, target_x, target_y):
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)

		dx = int(round(dx / distance))
		dy = int(round(dy / distance))
		self.move(dx, dy)

	def distance_to(self, other):
		#return the distance to another object
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)

	def send_to_back(self):
		global objects
		objects.remove(self)
		objects.insert(0, self)

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

				fighter_c = Fighter(hp=10,defense=0,power=3, death_function=monster_death)
				ai_c = BasicMonster()
				monster = GameObject(x, y, 'o', 'Orc', colours.desaturated_green, blocks=True, fighter=fighter_c, ai=ai_c)
			else:
				fighter_c = Fighter(hp=12,defense=1,power=3, death_function=monster_death)
				ai_c = BasicMonster()
				monster = GameObject(x, y, 'T', 'Troll', colours.darker_green, blocks=True, fighter=fighter_c, ai=ai_c)

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
		if obj.fighter and obj.x == x and obj.y == y:
			target = obj
			break

	if target is not None:
		player.fighter.attack(target)
	else:
		player.move(dx, dy)
		fov_recompute = True

def player_death(player):
	global game_state
	message('You Died!', colours.darkest_red)
	game_state = 'dead'

	player.char = '%'
	player.colour = colours.dark_red

def monster_death(monster):
	message(monster.name.capitalize() + ' is dead!', colours.blue)
	monster.char = '%'
	monster.colour = colours.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = monster.name + ' corpse'
	monster.send_to_back()

def message(new_msg, colour = colours.white):
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

	for line in new_msg_lines:
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]

		game_msgs.append((line, colour))

	y = 1
	for (line, colour) in game_msgs:
		panel.draw_str(MSG_X, y, line, bg=None, fg=colour)
		y += 1

def render_bar(x, y, total_width, name, value, maximum, bar_colour, back_colour):
	bar_width = int(float(value) / maximum * total_width)

	panel.draw_rect(x, y, total_width, 1, None, bg=back_colour)

	if bar_width > 0:
		panel.draw_rect(x, y, bar_width, 1, None, bg=bar_colour)

	text = name + ': ' + str(value) + '/' + str(maximum)
	x_centered = x + (total_width - len(text)) // 2
	panel.draw_str(x_centered, y, text, fg=colours.white, bg=None)




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
							con.draw_char(x,y,None,fg=None,bg=colour_dark_ground)
				else:
					if wall:
						con.draw_char(x, y, None, fg=None, bg=colour_light_wall)
					else:
						con.draw_char(x, y, None, fg=None, bg=colour_light_ground)
					my_map[x][y].explored = True


	for obj in objects:
		if obj != player:
			obj.draw()
	player.draw()

	

	render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, colours.dark_red, colours.darker_red)

	root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)
	root.blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0)

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
		return 'no-turn'

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
		elif key.key == 'SPACE' or key.key == 'KP5':
			player_move_or_attack(0, 0)
		else:
			return 'no-turn'

#===========================================================#
# Init and Main loop
#===========================================================#
tdl.set_font('terminal12x12_gs_ro.png', greyscale=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title='Unnamed Roguelike', fullscreen=False)
tdl.setFPS(LIMIT_FPS)

#main blit console
con = tdl.Console(MAP_WIDTH, MAP_HEIGHT)

game_state = 'playing'
player_action = None

fighter_component = Fighter(hp=30, defense=2, power=5, death_function=player_death)
player = GameObject(0, 0, 1, 'player', colours.white, blocks=True, fighter=fighter_component)
objects = [player]

panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)
panel.clear(fg=colours.white, bg=colours.black)

game_msgs = []

message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', colours.red)


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
			if obj.ai:
				obj.ai.take_turn()

	if player_action == 'exit':
		break

