import tdl
import colours
import math
import textwrap
from random import randint

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

		#No tile starts explored
		self.explored = False

		#Any blocking tile should also block sight
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
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' damage.')
			target.fighter.take_damage(damage)
		else:
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

	def heal(self, amount):
		self.hp += amount

		if self.hp > self.max_hp:
			self.hp = self.max_hp

class BasicMonster:
	def take_turn(self):
		monster = self.owner

		if(monster.x, monster.y) in visible_tiles:
			if monster.distance_to(player) >= 2:
				monster.move_towards(player.x, player.y)
			elif player.fighter.hp > 0:
				monster.fighter.attack(player)

class ConfusedMonster:
	
	def __init__(self, old_ai, num_turns=5):
		self.old_ai = old_ai
		self.num_turns = num_turns

	def take_turn(self):
		if self.num_turns > 0:
			if randint(1, 100) < 33 and self.owner.distance_to(player) < 2:
				monster.fighter.attack(player)
			else:
				self.owner.move(randint(-1, 1), randint(-1, 1))
				self.num_turns -= 1

		else:
			self.owner.ai = self.old_ai
			message('The ' + self.owner.name + ' is no longer confused.', colours.red)

class Item:

	def __init__(self, use_function=None):
		self.use_function = use_function

	def use(self):
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')
		else:
			result = self.use_function()
			if result != ('cancelled' or 'permanent'):
				inventory.remove(self.owner) #destory one use items

	def pick_up(self):
		if len(inventory) >= 52:
			message('Your inventory is full, cannot pick up ' + self.owner.name + '.', colours.red)
		else:
			inventory.append(self.owner)
			objects.remove(self.owner)
			message('You picked up a ' + self.owner.name + '!', colours.green)


class GameObject:

	def __init__(self, x, y, char, name, colour, blocks=False, fighter=None, ai=None, item=None):
		self.name = name
		self.blocks = blocks
		self.x = x
		self.y = y
		self.char = char
		self.colour = colour

		self.fighter = fighter
		if self.fighter:
			self.fighter.owner = self

		self.item = item
		if self.item:
			self.item.owner = self

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
		global visible_tiles

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
		x = randint(room.x1 + 1, room.x2 - 1)
		y = randint(room.y1 + 1, room.y2 - 1)

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

	num_items = randint(0, MAX_ROOM_ITEMS)

	for i in range(num_items):
		x = randint(room.x1 + 1, room.x2 - 1)
		y = randint(room.y1 + 1, room.y2 - 1)

		if not is_blocked(x, y):
			num = randint(0, 100)
			if num < 70:

				item_component = Item(use_function=cast_heal)
				item = GameObject(x, y, '!', 'healing potion', colours.violet, item=item_component)
			elif num < 70+15:
				item_component = Item(use_function=cast_lightning)

				item = GameObject(x, y, '#', 'Bolt Scroll', colours.light_yellow, item=item_component)
			else:
				item_component = Item(use_function=cast_lightning)

				item = GameObject(x, y, '#', 'Confuse Scroll', colours.yellow, item=item_component)


			objects.append(item)

			item.send_to_back()

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

def cast_heal():
		#heal the player
		if player.fighter.hp == player.fighter.max_hp:
			message('You are already at full health.', colours.red)
			return 'cancelled'
		message('Your wounds start to feel better!', colours.light_violet)
		player.fighter.heal(int(player.fighter.max_hp * 0.25))

def cast_lightning():
	monster = closest_monster(5)


	if monster is None:
		message('No ememy is close enough to strike.', colours.red)
		return 'cancelled'

	message('A bolt of lightning strikes the ' + monster.name + ' with a loud zap! You deal ' + str(20) + ' damage.', colours.light_blue)
	monster.fighter.take_damage(20)

def cast_confuse():
	monster = closest_monster(7)

	if monster is None:
		message('No ememy is close enough to confuse.', colours.red)
		return 'cancelled'

	old_ai = monster.ai
	monster.ai = ConfusedMonster(old_ai)
	monster.ai.owner = monster
	message('A fugue comes over the ' + monster.name + '!', colours.light_green)


def closest_monster(max_range):
	closest_enemy = None
	closest_dist = max_range + 1

	for obj in objects:
		if obj.fighter and not obj == player and (obj.x, obj.y) in visible_tiles:
			dist = player.distance_to(obj)

			if dist < closest_dist:
				closest_enemy = obj
				closest_dist = dist

	return closest_enemy



def player_move_or_attack(dx, dy):
	global fov_recompute
	global game_state

	game_state = 'playing'

	x = player.x + dx
	y = player.y + dy

	target = None
	for obj in objects:
		if obj.fighter and obj.x == x and obj.y == y:
			if obj != player:
				target = obj
			break

	if target is not None:
		player.fighter.attack(target)
	else:
		player.move(dx, dy)
		fov_recompute = True

def player_death(player):
	global game_state
	message('You Died!', colours.red)
	game_state = 'dead'

	player.char = '%'
	player.colour = colours.dark_red

def get_names_under_mouse():
	global visible_tiles
	global mouse_coord

	(x, y) = mouse_coord

	names = [obj.name for obj in objects
		if obj.x == x and obj.y == y and (obj.x, obj.y) in visible_tiles]


	names = ', '.join(names)
	return names.capitalize() 

def monster_death(monster):
	message(monster.name.capitalize() + ' is dead!', colours.orange)
	monster.char = '%'
	monster.colour = colours.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = monster.name + ' corpse'
	monster.send_to_back()

def menu(header, options, width):
	if len(options) > 52: raise ValueError('Cannot have a menu with more than 52 options')

	header_wrapped = textwrap.wrap(header, width)
	header_height = len(header_wrapped)
	height = len(options) + header_height

	window = tdl.Console(width, height)

	window.draw_rect(0, 0, width, height, None, fg=colours.white, bg=None)

	for i, line in enumerate(header_wrapped):
		window.draw_str(0, 0 + i, header_wrapped[i])

		y = header_height
		letter_index = ord('a')
		for option_text in options:
			text = '(' + chr(letter_index) + ')' + option_text
			window.draw_str(0, y, text, bg=None)
			y += 1
			letter_index += 1
			if letter_index == ord('z'):
				letter_index = ord('A')

		x = SCREEN_WIDTH//2 - width//2
		y = SCREEN_HEIGHT//2 - height//2
		root.blit(window, x, y, width, height, 0, 0)

		tdl.flush()
		key = tdl.event.key_wait()
		key_char = key.char
		if key_char == '':
			key_char = ' '

		index = ord(key_char) - ord('a')
		if index > 26:
			index = ord(key_char) - ord('A')

		if index >= 0 and index < len(options):
			return index

		return None


def inventory_menu(header):
	if len(inventory) == 0:
		options = ['Inventory is empty.']
	else:
		options = [item.name for item in inventory]

	index = menu(header, options, INVENTORY_WIDTH)

	if index is None or len(inventory) == 0: return None
	return inventory[index].item



def message(new_msg, colour = colours.white):
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

	for line in new_msg_lines:
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]

		game_msgs.append((line, colour))


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
		visible_tiles = tdl.map.quickFOV(player.x, player.y, 
										is_visible_tile, 
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

					#add visible tile as explored
					my_map[x][y].explored = True


	for obj in objects:
		if obj != player:
			obj.draw()
	player.draw()

	#blit all we've drawn so far onto the root console
	root.blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0)

	#GUI Panel cleared for redraw
	panel.clear(fg=colours.white, bg=colours.black)

	#Print out all game messages
	y = 1
	for (line, colour) in game_msgs:
		panel.draw_str(MSG_X, y, line, bg=None, fg=colour)
		y += 1

	#Statbar
	render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, colours.dark_red, colours.darker_red)

	#Contents under mouse
	panel.draw_str(1, 0, get_names_under_mouse(), bg=None, fg=colours.light_gray)

	#Blit the GUI Panel to the console
	root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)
	

#Key Handler
def handle_keys():
	global fov_recompute
	global game_state
	global mouse_coord


	keypress = False
	for event in tdl.event.get():
		if event.type == 'KEYDOWN':
			key = event
			keypress = True
		if event.type == 'MOUSEMOTION':
			mouse_coord = event.cell
	if not keypress:
		return 'no-turn'

	if key.key == '?':
		game_state = 'help'
		return 'help'

	if key.key == 'ENTER' and key.alt:
		tdl.set_fullscreen(not tdl.get_fullscreen())

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
			if key.text == 'g':
				#pick up item
				for obj in objects:
					if obj.x == player.x and obj.y == player.y and obj.item:
						obj.item.pick_up()
						break
			elif key.text == 'i':
				chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.use()
			return 'no-turn'

#===========================================================#
# Init and Main loop
#===========================================================#
tdl.set_font('terminal12x12_gs_ro.png', greyscale=True)
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title='Unnamed Roguelike', fullscreen=False)
tdl.setFPS(LIMIT_FPS)
tdl.force_resolution(1920, 1080)

#main blit console
con = tdl.Console(MAP_WIDTH, MAP_HEIGHT)

game_state = 'playing'
player_action = None

fighter_component = Fighter(hp=30, defense=2, power=5, death_function=player_death)
player = GameObject(0, 0, 1, 'player', colours.black, blocks=True, fighter=fighter_component)
objects = [player]

panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)
panel.clear(fg=colours.white, bg=colours.black)


inventory = []
game_msgs = []

message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', colours.red)


mouse_coord = (0,0)

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

