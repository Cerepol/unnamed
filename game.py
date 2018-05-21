"""This is a shitty unnamed roguelike project"""
import math
import textwrap
import shelve
import os
from random import randint

from bearlibterminal import terminal as t
from tdl.map import quickFOV
import colours
from constants import *
import gamemap as gmap
import player
import render

DIR = dict([(t.TK_J, (0, -1)), (t.TK_K, (0, 1)), (t.TK_H, (-1, 0)), (t.TK_L, (1, 0)), 
				(t.TK_Y, (-1, -1)), (t.TK_U, (1, -1)), (t.TK_B, (-1, 1)), (t.TK_N, (1, 1)),
				(t.TK_KP_8, (0, -1)), (t.TK_KP_2, (0, 1)), (t.TK_KP_4, (-1, 0)), (t.TK_KP_6, (1, 0)), 
				(t.TK_KP_7, (-1, -1)), (t.TK_KP_9, (1, -1)), (t.TK_KP_1, (-1, 1)), (t.TK_KP_3, (1, 1)),
				(t.TK_SPACE, (0, 0)), (t.TK_KP_5, (0, 0))])

###########
# GLOBALS #
###########
fov_recompute = True
game_state = 'playing'
inventory = []
game_msgs = []
objects = []
visible_tiles = []
player = None
turn_count = 0
dungeon_level = 0
savename = SAVE_PATH
stairs = []


###################
# Game Components #
###################

class GameObject:
	"""Basic GameObject

	Uses an optional component system to define behaviour and purpose
	"""
	# pylint: disable=too-many-instance-attributes
	def __init__(self, x, y, char, name, rgb, blocks=False, always_visible=False, fighter=None, ai=None, item=None, portal=None):
		# pylint: disable=too-many-arguments
		global dungeon_level

		self.name = name
		self.blocks = blocks
		self.x = x
		self.y = y
		self.char = char
		self.rgb = rgb
		self.portal = portal
		self.dungeon_level = dungeon_level
		self.always_visible = always_visible

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
		"""Moves the object by the x,y deltas"""
		if not gmap.is_blocked(self.x + dx, self.y + dy, objects):
			self.x += dx
			self.y += dy

	def move_towards(self, target_x, target_y):
		"""Automatically guides the object towards the point"""
		dx = target_x - self.x
		dy = target_y - self.y

		distance = math.sqrt(dx ** 2 + dy ** 2)

		dx = int(round(dx / distance))
		dy = int(round(dy / distance))

		self.move(dx, dy)

	def distance(self, x, y):
		"""Returns the distance to an x and y"""
		return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

	def distance_to(self, other):
		"""return the distance to another object"""
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)

	def send_to_back(self):
		"""Purposefully adds this item to the back of the objects list"""
		global objects
		objects.remove(self)
		objects.insert(0, self)

	def draw(self):
		"""Draws self onto the terminal"""
		global visible_tiles

		if (self.x, self.y) in visible_tiles or \
			(self.always_visible and gmap.is_explored(self.x, self.y)):
			set_colour(self.rgb, 255)
			t.put(self.x, self.y, self.char)
			#con.draw_char(self.x, self.y, self.char, self.colour, bg=None)

	def clear(self):
		"""Clears self off the board"""
		t.put(self.x, self.y, ' ')
		#con.draw_char(self.x, self.y, ' ', self.colour, bg=None)

class Player(GameObject):
	"""Player Class"""

	def __init__(self, x, y, char, name, rgb, xp=0, level=0, fighter=None, progression=None):
		# pylint: disable=too-many-arguments
		#         x, y, char, name, rgb, blocks=False, always_visible=False, fighter=None
		super().__init__(x, y, char, name, rgb, blocks=True, always_visible=True, fighter=fighter)
		self.xp = xp
		self.level = level
		self.progression = progression

		if self.fighter:
			self.fighter.attack = self.attack

	def attack(self, target):
		"""Launches an attack against the target"""
		damage = self.fighter.power - target.fighter.defense

		if damage > 0:			
			message('You attack '  
					+ target.name + ' for ' + str(damage) + ' damage.') 
			dead = target.fighter.take_damage(damage)

			#take_damage returns the monsters XP, or false if it doesn't die
			#For a number to return false it has to be 0 which means as long as its dead and gives xp
			if dead:
				print(dead)
				self.xp += dead
				#TODO check for level increase.
		else:
			message('Your attack has no effect!') 

class Fighter:
	"""Fighter component

	This component is necessary for any gameobject to engage in fighting
	death_function is used to cleanup upon death, such as leaving a corpse	
	"""

	def __init__(self, hp, defense, power, xp=1, death_function=None):
		# pylint: disable=too-many-arguments
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power
		self.xp = xp
		self.death_function = death_function

	def take_damage(self, damage):
		"""Damages the actor for the specificed amount, calls death_function if available"""
		if damage > 0:
			self.hp -= damage

		if self.hp <= 0:
			function = self.death_function
			if function is not None:
				#Owner is set by GameObject which is required for this to be accessed
				function(self.owner)
				return self.xp
		return False

	def attack(self, target):
		"""Launches an attack against the target"""
		damage = self.power - target.fighter.defense

		if damage > 0:			
			message(self.owner.name.capitalize() + ' attacks '  
											+ target.name + ' for ' + str(damage) + ' damage.') 
			target.fighter.take_damage(damage)
		else:
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!') 

	def heal(self, amount):
		"""Heals self for specificed amount"""
		self.hp += amount

		if self.hp > self.max_hp:
			self.hp = self.max_hp

class BasicMonster:
	"""Basic Monster AI, can take own turn"""

	def take_turn(self):
		"""Takes turn towards the player if visible"""
		monster = self.owner 

		if(monster.x, monster.y) in visible_tiles:
			if monster.distance_to(player) >= 2:
				monster.move_towards(player.x, player.y)
			elif player.fighter.hp > 0:
				monster.fighter.attack(player)

class ConfusedMonster:
	"""Replacement AI for confused AI"""

	def __init__(self, old_ai, num_turns=5):
		self.old_ai = old_ai
		self.num_turns = num_turns

	def take_turn(self):
		"""Confused TakeTurn, move with chance of attack if beside player"""
		if self.num_turns > 0:
			if randint(1, 100) < 33 and self.owner.distance_to(player) < 2:
				self.owner.fighter.attack(player)
			else:
				self.owner.move(randint(-1, 1), randint(-1, 1))
				self.num_turns -= 1

		else:
			self.owner.ai = self.old_ai
			message('The ' + self.owner.name + ' is no longer confused.', colours.red)

class Item:
	"""Basic Item Class, contains methods for pickup and use"""

	def __init__(self, use_function=None):
		self.use_function = use_function

	def use(self):
		"""Use function, calls the assigned use_function"""
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.') 

		else:
			result = self.use_function()
			if result != 'cancelled':
				inventory.remove(self.owner)
				return True
			return False

	def pick_up(self):
		"""Places item in inventory if picked up by player"""
		if len(inventory) >= 52:
			message('Your inventory is full, cannot pick up ' + self.owner.name + '.', colours.red)
		else:
			inventory.append(self.owner) 
			objects.remove(self.owner)
			message('You picked up a ' + self.owner.name + '!', colours.green)

	def drop(self):
		"""Drops item onto the players current position"""
		objects.append(self.owner)
		inventory.remove(self.owner)

		self.owner.x = player.x
		self.owner.y = player.y

		message('You dropped a ' + self.owner.name + '.'. colours.yellow)

class Portal:
	"""Portal class, used for set teleporting between levels/coordinates"""
	def __init__(self, x, y, level):
		self.x = x
		self.y = y
		self.level = level

	def enter(self, obj):
		"""Moves the object to the portal coordinates"""
		obj.x = self.x
		obj.y = self.y
		if obj.level != self.level:
			move_object(obj, self.level)



def place_objects(room):
	"""places objects like monsters and items into the room"""
	num_monsters = randint(0, MAX_ROOM_MONSTERS)

	for i in range(num_monsters):
		x = randint(room.x1 + 1, room.x2 - 1)
		y = randint(room.y1 + 1, room.y2 - 1)

		if not gmap.is_blocked(x, y, objects):
			if randint(0, 100) < 80:

				fighter_c = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
				ai_c = BasicMonster()
				monster = GameObject(x, y, chr(7), 'blob', colours.desaturated_green, blocks=True, 
									fighter=fighter_c, ai=ai_c)
			else:
				fighter_c = Fighter(hp=12, defense=1, power=3, death_function=monster_death)
				ai_c = BasicMonster()
				monster = GameObject(x, y, chr(4), 'Big blob', colours.darker_green, 
					blocks=True, fighter=fighter_c, ai=ai_c)

			objects.append(monster)

	num_items = randint(0, MAX_ROOM_ITEMS)

	for i in range(num_items):
		x = randint(room.x1 + 1, room.x2 - 1)
		y = randint(room.y1 + 1, room.y2 - 1)

		if not gmap.is_blocked(x, y, objects):
			num = randint(0, 100)
			if num < 55:
				item_component = Item(use_function=cast_heal)
				item = GameObject(x, y, '!', 'healing potion', colours.violet, item=item_component, always_visible=True)

			elif num < 55+15:
				item_component = Item(use_function=cast_lightning)
				item = GameObject(x, y, '#', 'Bolt Scroll', colours.light_blue, item=item_component, always_visible=True)

			elif num < 55+15+15:
				item_component = Item(use_function=cast_confuse)
				item = GameObject(x, y, '#', 'Confuse Scroll', colours.blue, item=item_component, always_visible=True)

			elif num <= 55+15+15+15:
				item_component = Item(use_function=cast_fireball)
				item = GameObject(x, y, '#', 'Fireball Scroll', colours.dark_blue, item=item_component, always_visible=True)


			objects.append(item)

			item.send_to_back()

def closest_monster(max_range):
	"""Finds the closest monster within range"""
	closest_enemy = None
	closest_dist = max_range + 1

	for obj in objects:
		if obj.fighter and obj != player and (obj.x, obj.y) in visible_tiles:
			dist = player.distance_to(obj)

			if dist < closest_dist:
				closest_enemy = obj
				closest_dist = dist

	return closest_enemy

def target_monster(max_range=None):
	"""Selects specifically one monster, wrapper for target_tile"""

	(x, y) = target_tile(max_range)

	if x is None:
		return None

	for obj in objects:
		if obj.x == x and obj.y == y and obj.fighter and obj != player:
			return obj

def target_tile(max_range=None):
	"""Selects a tile either from a mouse click or selection"""

	x = player.x
	y = player.y
	mx = t.state(t.TK_MOUSE_X)
	my = t.state(t.TK_MOUSE_Y)

	render.draw_cursor(x, y)
	render.draw_max_range(player, max_range)

	message("Select using the mouse or movements keys. Use M1, Enter, 5 to confirm and ESC/SPACE to cancel", colours.light_cyan)
	render_all()

	key = t.read()
	while key not in (t.TK_MOUSE_LEFT, t.TK_ENTER, t.TK_KP_ENTER, t.TK_KP_5, t.TK_ESCAPE, t.TK_SPACE):
		dx = x
		dy = y
		if key in DIR:
			(dir_x, dir_y) = DIR.get(key)
			dx += dir_x
			dy += dir_y
		zx = t.state(t.TK_MOUSE_X)
		zy = t.state(t.TK_MOUSE_Y)
		if zx != mx or zy != my:
			mx = zx
			my = zy
			dx = mx
			dy = my

		#Check for Out of Bounds/Range
		if 0 < dx and dx < MAP_WIDTH and 0 < dy and dy < MAP_HEIGHT:
			#Check for within range
			if player.distance(dx, dy) <= max_range and not gmap.is_blocked(dx, dy, None, tilesOnly=True) \
							and gmap.is_explored(dx, dy):
				x = dx
				y = dy

		render.draw_cursor(x, y)
		if t.has_input():
			key = t.read()
		else:
			key = None

	#Check if it was a mouse confirm or a key confirm/cancel
	render.draw_cursor(None, None)
	render.draw_max_range(None, None)
	if key == t.TK_MOUSE_LEFT:
		x = t.state(t.TK_MOUSE_X)
		y = t.state(t.TK_MOUSE_Y)
	#Cancel selection process
	elif key in (t.TK_ESCAPE, t.TK_SPACE):
		return (None, None)
	#Return coordinates selected
	return (x, y)

def level_up():
	"""Checks for Player levelup"""
	#TODO check for levelup
	return

def get_names_under_mouse():
	"""Returns name of objects under the mouse cursor"""
	global visible_tiles

	x = t.state(t.TK_MOUSE_X)
	y = t.state(t.TK_MOUSE_Y)

	#A little complicated
	#Check that the object is at the mouses coordinates
	#Check if either, the object is on an explored tile and is always_visible once explored
	#OR check if its actually within the visible tiles
	names = [obj.name for obj in objects
		if obj.x == x and obj.y == y and 
		((gmap.is_explored(obj.x, obj.y) and obj.always_visible) or (obj.x, obj.y) in visible_tiles)]
	names += [obj.name for obj in stairs if obj.x == x and obj.y == y and gmap.is_explored(obj.x, obj.y)]

	names = ', '.join(names)
	return names.capitalize() 

def make_map():
	"""Makes the map out of tiles"""
	global objects, stairs

	gmap.Map = [[gmap.Tile(True)
		for y in range(MAP_HEIGHT)]
			for x in range(MAP_WIDTH)]

	#Refresh the obj list.
	objects = [player]

	rooms = []
	num_rooms = 0

	for r in range(MAX_ROOMS):
		w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		x = randint(0, MAP_WIDTH - w - 1)
		y = randint(0, MAP_HEIGHT - h - 1)

		new_room = gmap.Rect(x, y, w, h)
		failed = False
		for other_room in rooms:
			if new_room.intersect(other_room):
				failed = True
				break

		if not failed:

			gmap.create_room(new_room)

			(new_x, new_y) = new_room.center()

			if num_rooms == 0:
				player.x = new_x
				player.y = new_y

			else:
				(prev_x, prev_y) = rooms[num_rooms - 1].center()

				if randint(0, 1):
					gmap.create_h_tunnel(prev_x, new_x, prev_y)
					gmap.create_v_tunnel(prev_y, new_y, new_x)
				else:
					gmap.create_v_tunnel(prev_y, new_y, prev_x)
					gmap.create_h_tunnel(prev_x, new_x, new_y)
			
			place_objects(new_room)

			rooms.append(new_room)
			num_rooms += 1

	portal_component = Portal(dungeon_level + 1, None, None)		
	stair = GameObject(new_x, new_y, '>', 'stairs', colours.white, portal=portal_component, always_visible=True)

	

	stairs = []
	stairs.append(stair)
	message("stairs at: " + str(stair.x) + ' ' + str(stair.y))

#########################
# Item/Player Functions #
#########################
def set_colour(rgb, alpha=255):
	"""Wrapper for bearlibterminal color method, so I can spell properly"""	
	hexcolour = alpha
	hexcolour = hexcolour * 256 + rgb[0]
	hexcolour = hexcolour * 256 + rgb[1]
	hexcolour = hexcolour * 256 + rgb[2]
	t.color(hexcolour)

def set_bkcolour(rgb, alpha=255):
	"""Wrapper for the bearlibterminal bkcolor method, so I can spell properly"""
	hexcolour = alpha
	hexcolour = hexcolour * 256 + rgb[0]
	hexcolour = hexcolour * 256 + rgb[1]
	hexcolour = hexcolour * 256 + rgb[2]
	t.color(hexcolour)

def cast_heal():
	"""Heals the user for an amount"""
	if player.fighter.hp == player.fighter.max_hp:
		message('You are already at full health.', colours.red)
		return 'cancelled'
	message('Your wounds start to feel better!', colours.light_violet)
	player.fighter.heal(int(player.fighter.max_hp * 0.25))

def cast_lightning():
	"""Does ranged damage to the closest enemy"""
	monster = closest_monster(5)

	if monster is None:
		message('No ememy is close enough to strike.', colours.red)
		return 'cancelled'

	message('A bolt of lightning strikes the ' + monster.name + 
									' with a loud zap! You deal ' + str(20) + ' damage.', colours.light_blue)
	monster.fighter.take_damage(20)

def cast_fireball():
	"""Player targeted aoe spell"""
	(x, y) = target_tile(6)
	if x is None:
		message("Cancelled")
		return 'cancelled'
	message('The fireball explodes!', colours.orange)

	t.layer(EFFECT_LAYER)

	effected_points = render.draw_fireball(x, y)

	for obj in objects:
		if (obj.x, obj.y) in effected_points and obj.fighter:
			message('The ' + obj.name + ' takes 15 damage.', colours.orange)
			obj.fighter.take_damage(15)


def cast_confuse():
	"""Replaces normal AI with Confused AI"""
	monster = target_monster(3)

	if monster is None:
		message('Cancelled', colours.red)
		return 'cancelled'

	old_ai = monster.ai
	monster.ai = ConfusedMonster(old_ai)
	monster.ai.owner = monster
	message('A fugue comes over the ' + monster.name + '!', colours.light_green)

def player_move_or_attack(dx, dy):
	"""Figures out if the player is moving or attacking"""
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

def monster_death(monster):
	"""Basic Monster Death funciton"""
	message(monster.name.capitalize() + ' is dead!', colours.orange)
	monster.char = '%'
	monster.rgb = colours.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = monster.name + ' corpse'
	monster.send_to_back()

def player_death(player):
	"""Normal Player Death function"""
	global game_state
	message('You Died!', colours.red)
	game_state = 'dead'

	player.char = '%'
	player.rgb = colours.dark_red

################
# UI Functions #
################
def menu(header, options, width):
	"""Creates a menu"""
	if len(options) > 52: 
		raise ValueError('Cannot have a menu with more than 52 options')

	header_wrapped = textwrap.wrap(header, width)
	header_height = len(header_wrapped)
	height = len(options) + header_height

	x = SCREEN_WIDTH//2 - width//2
	y = SCREEN_HEIGHT//2 - height//2
	t.layer(MENU_UNDERLAYER)
	set_colour(colours.dark_grey, 200)
	if len(options) >= 1:
		width += 3 #+3 adds room for (a) being present on every option
	t.puts(x - 1, y - 1, BLOCK_CHAR * (width + 2) * (height + 2), width=width+2, height=height+2)

	#Draw the header out.
	set_colour(colours.white)
	t.layer(MENU_LAYER)
	for i, line in enumerate(header_wrapped):
		t.puts(x, y + i, line)

	y += header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ')' + option_text
		t.puts(x, y, text)

		y += 1
		letter_index += 1
		if letter_index == ord('z'):
			letter_index = ord('A')

	t.refresh()
	t.clear_area(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
	t.layer(MENU_UNDERLAYER)
	t.clear_area(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

	if options:
		key = t.read()
		while key == t.TK_MOUSE_MOVE:
			key = t.read()

		index = key - 4
		if index >= 0 and index <= 25:
			if t.state(t.TK_SHIFT):
				index += 26

		if index < len(options):
			return index
	
	return None

def msgbox(text, width=50):
	"""Displays a message box with text"""
	menu(text, [], width)

	key = t.read()
	while key == t.TK_MOUSE_MOVE:
		key = t.read()


def inputbox(text, width=50):
	"""Gathers user input"""
	menu(text, [], width)

	y = SCREEN_HEIGHT//2
	x = SCREEN_WIDTH//2 - width//2

	t.layer(MENU_LAYER)
	
	user_input = ""

	key = t.read()
	while key not in (t.TK_ENTER, t.TK_KP_ENTER):
		if t.state(t.TK_CHAR):
			letter = char_from_index(key)
			if letter is not None:
				user_input += letter
				t.layer(MENU_UNDERLAYER)
				set_colour(colours.dark_grey, 200)
				t.puts(x, y - 1, BLOCK_CHAR * 3, 1, 3)

				t.layer(MENU_LAYER)
				set_colour(colours.white)
				t.put(x, y, letter)
				x += 1
				t.refresh()
		elif key == t.TK_BACKSPACE:
			if user_input:
				user_input = user_input[:-1]
				x -= 1
				t.clear_area(x, y - 1, 1, 3)
				t.refresh()

		key = t.read()

	#Return user input
	return user_input


def char_from_index(key_code):
	"""Converts a BTL key code into a alpha character is possible"""

	if key_code == t.TK_SPACE:
		return ' '

	index = key_code - 4
	letter = None

	if index >= 0 and index <= 25:
		letter = chr(ord('a') + index)

		if t.state(t.TK_SHIFT):
			letter = letter.upper()

	return letter


def inventory_menu(header):
	"""Defines an inventory menu"""

	if not inventory:
		options = ['Inventory is empty.']
	else:
		options = [item.name for item in inventory]

	index = menu(header, options, INVENTORY_WIDTH)

	if index is None or not inventory: 
		return None
	return inventory[index].item



def message(new_msg, colour=colours.white):
	"""Creates a new message for the message log"""

	set_colour(colour)
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

	for line in new_msg_lines:
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]

		game_msgs.append((line, colour))


def render_bar(x, y, total_width, name, value, maximum, bar_colour, back_colour):
	"""Renders UI Bar"""
	bar_width = int(float(value) / maximum * total_width)
	
	fill = BLOCK_CHAR * total_width

	t.layer(UI_LAYER)
	set_colour(back_colour)
	t.puts(x, y, fill, width=total_width, height=1)
	#panel.draw_rect(x, y, total_width)

	if bar_width > 0:
		set_colour(bar_colour)
		t.puts(x, y, fill, width=bar_width, height=1)
		#panel.draw_rect(x, y, bar_width, 1, None, bg=bar_colour)

	text = name + ': ' + str(value) + '/' + str(maximum)
	x_centered = x + (total_width - len(text)) // 2

	t.layer(UI_TEXT_LAYER)
	set_colour(colours.white)
	t.puts(x_centered, y, text)


def render_all():
	"""Goes through object list and renders everything"""
	global fov_recompute
	global visible_tiles

	if fov_recompute:
		fov_recompute = False
		visible_tiles = quickFOV(player.x, player.y,
								gmap.is_visible_tile,
								fov=FOV_ALGO,
								radius=TORCH_RADIUS,
								lightWalls=FOV_LIGHT_WALLS,
								sphere=False)

		#Set to the background layer before drawing the area
		t.layer(BASE_LAYER)

		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				set_colour(colours.black, 255)
				visible = (x, y) in visible_tiles
				wall = gmap.Map[x][y].block_sight
				if not visible:
					if gmap.Map[x][y].explored:
						if wall:
							set_colour(colours.darkest_gray, 255)
						else:
							set_colour(colours.darker_gray, 255)
							
				else:
					if wall:
						set_colour(colours.gray, 255)
					else:
						set_colour(colours.light_gray, 255)

					#add visible tile as explored
					gmap.Map[x][y].explored = True
				#Draw the character on the map
				t.put(x, y, BLOCK_CHAR)

	t.layer(OBJECT_LAYER)
	for obj in objects:
		if obj != player:
			obj.draw()
	for stair in stairs:
		stair.draw()
	player.draw()

	#GUI Panel cleared for redraw
	#panel.clear(fg=colours.white, bg=colours.black)

	#Print out all game messages
	t.layer(UI_TEXT_LAYER)
	t.clear_area(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

	y = PANEL_Y
	for (line, colour) in game_msgs:
		set_colour(colour)
		t.puts(MSG_X, y, line)
		#panel.draw_str(MSG_X, y, line, bg=None, fg=colour)
		y += 1

	#Contents under mouse
	set_colour(colours.light_gray)
	t.puts(1, PANEL_Y - 1, get_names_under_mouse())

	#Statbar
	render_bar(1, PANEL_Y, BAR_WIDTH, 'HP', player.fighter.hp, 
				player.fighter.max_hp, colours.dark_red, colours.darker_red)

	t.refresh()

def handle_keys():
	"""All Key Handling for the game"""
	global fov_recompute, game_state, dungeon_level, objects, stairs

	keypress = False

	if t.has_input():
		key = t.read()
		if key != t.TK_MOUSE_MOVE:
			keypress = True

	if not keypress:
		return 'no-turn'

	if key == t.TK_SLASH and t.state(t.TK_SHIFT):
		return 'help'

	if key == t.TK_ESCAPE:
		return 'exit'

	if game_state == 'playing':
		fov_recompute = True

		if key in DIR:
			(x, y) = DIR.get(key)
			player_move_or_attack(x, y)
		else:
			if key == t.TK_G:
				#pick up item
				for obj in objects:
					if obj.x == player.x and obj.y == player.y and obj.item:
						obj.item.pick_up()
						break
			elif key == t.TK_I:
				chosen_item = inventory_menu('Press the assigned key to use it, or any other to cancel.\n')
				if chosen_item is not None:
					if not chosen_item.use():
						return 'no-turn'

			elif key == t.TK_D:
				chosen_item = inventory_menu('Press the key next to an item to drop it. Any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.drop()
				else:
					return 'no-turn'
			elif key == t.TK_PERIOD and t.state(t.TK_SHIFT):
				for stair in stairs:
					if stair.x == player.x and stair.y == player.y and stair.char == '>':
						if not check_for_level(stair.portal.level):
							save_level()
							old_stairs = list(stairs)
							make_map()

							#Backlink the old stairs and save them
							if BACKTRACK:
								portal_component = Portal(player.x, player.y, dungeon_level + 1)
								stair.portal = portal_component
							save_stairs(old_stairs)

							#Create upstairs
							if BACKTRACK:
								portal_component = Portal(stair.x, stair.y, dungeon_level)
								return_stair = GameObject(player.x, player.y, '<', 'stairs', colours.white, portal=portal_component, always_visible=True)
							else:
								return_stair = GameObject(player.x, player.y, chr(240), 'Sealed Hatch', colours.white, always_visible=True)

							#Set the new dungeon level
							dungeon_level = stair.portal.level

							stairs.append(return_stair)
							break
						else:
							load_old_level(stair.portal)
							break
			elif key == t.TK_COMMA and t.state(t.TK_SHIFT):
				for stair in stairs:
					if stair.x == player.x and stair.y == player.y and stair.char == '<':
						load_old_level(stair.portal)
						break
			elif key == t.TK_C:
				#TODO Display character stats
				return 'no-turn'
			else:
				return 'no-turn'
		return 'turn'

def move_object(obj, level):
	"""Moves objects between levels"""
	global objects, savename

	with shelve.open(savename, 'c') as save:
		obj.level = level
		objname = 'objects' + str(level)
		stuff = save[objname]

		if not stuff:
			stuff = []
		stuff.append(obj)

		objects.remove(obj)
		
		save.close()

def save_stairs(stairs):
	"""Save the stairs after modiftying"""
	global savename, dungeon_level

	with shelve.open(savename, 'c') as save:
		stairname = 'stairs' + str(dungeon_level)
		save[stairname] = stairs

def save_level():
	"""Saves the current level"""
	global savename, dungeon_level, player

	with shelve.open(savename, 'c') as save:
		mapname = 'my_map' + str(dungeon_level)
		save[mapname] = gmap.Map

		objects.remove(player)
		objname = 'objects' + str(dungeon_level)
		save[objname] = objects


def check_for_level(level):
	"""Checks if a given level exists"""
	global savename

	with shelve.open(savename, 'c') as save:
		mapname = 'my_map' + str(level)
		value = True
		if mapname not in save:
			value = False
		save.close()
		return value

def load_old_level(portal):
	"""Loads a previously generated level"""
	global dungeon_level, stairs
	save_level()
	save_stairs(stairs)
	player.x = portal.x
	player.y = portal.y
	dungeon_level = portal.level
	load_level(dungeon_level)

def load_level(level):
	"""Loads the a level"""
	global savename, objects, stairs

	with shelve.open(savename, 'c') as save:
		mapname = 'my_map' + str(level)
		if mapname not in save:
			return False
		gmap.Map = save[mapname]

		objname = 'objects' + str(level)
		objects = save[objname]
		objects.append(player)

		stairname = 'stairs' + str(dungeon_level)
		stairs = save[stairname]

		save.close()

	return True


def load_game():
	"""Loads the game state"""
	global objects, player, inventory, game_msgs, game_state, savename, dungeon_level, stairs

	saves = os.listdir(SAVE_PATH)
	saves = [i.split(sep=".")[0] for i in saves]
	saves = list(set(saves))

	option = menu("Choose a Save", saves, 50)

	savename = SAVE_PATH + saves[option]

	with shelve.open(savename, 'r') as save:
		dungeon_level = save['dungeon_level']

		mapname = 'my_map' + str(dungeon_level)
		gmap.Map = save[mapname]

		stairname = 'stairs' + str(dungeon_level)
		stairs = save[stairname]

		objname = 'objects' + str(dungeon_level)
		objects = save[objname]
		player = objects[save['player_index']]

		inventory = save['inventory']
		game_msgs = save['game_msgs']
		game_state = save['game_state']

		save.close()

def save_game():
	"""Saves the games state to a file"""
	global savename, dungeon_level

	with shelve.open(savename, 'c') as save:
		save['dungeon_level'] = dungeon_level

		mapname = 'my_map' + str(dungeon_level)
		save[mapname] = gmap.Map

		objname = 'objects' + str(dungeon_level)
		save[objname] = objects

		stairname = 'stairs' + str(dungeon_level)
		save[stairname] = stairs

		save['player_index'] = objects.index(player)		
		save['inventory'] = inventory
		save['game_msgs'] = game_msgs
		save['game_state'] = game_state

		save.close()

def new_game():
	"""Creates a new game state"""
	global player, inventory, game_msgs, game_state, dungeon_level, savename

	#Get the player name
	name = inputbox("Enter a player name", 20)
	if name == "":
		name = 'Player'

	fighter_component = Fighter(hp=30, defense=2, power=8, 
						death_function=player_death)
	player = Player(0, 0, 2, name, colours.black, fighter=fighter_component, progression=None)

	#Prepare the game world
	dungeon_level = 1
	make_map()
	t.clear()

	message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', colours.red)

	item_component = Item(use_function=cast_fireball)
	item = GameObject(-1, -1, '#', 'Fireball Scroll', colours.dark_blue, item=item_component)
	objects.append(item)
	item.item.pick_up()

def play_game():
	"""Starts the game up"""
	global fov_recompute, savename

	player_action = None
	fov_recompute = True

	savename = SAVE_PATH + player.name

	while player_action != 'exit':
		render_all()

		player_action = handle_keys()


		t.layer(OBJECT_LAYER)
		t.clear_area(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
	
		if game_state == 'playing' and player_action not in ('no-turn', 'exit'):
			for obj in objects:
				if obj.ai:
					obj.ai.take_turn()

	save_game()

def main_menu():
	"""Main main for this game"""

	t.layer(0)
	set_colour(colours.white, 100)
	t.put(0, 0, 0x5E)
	#show the game's title, and some credits!

	
	title = 'Death and Axes'
	center = (SCREEN_WIDTH - len(title)) // 2

	t.layer(UI_LAYER)
	set_colour(colours.dark_azure, 150)
	t.puts(center - 1, SCREEN_HEIGHT//2 - 5, BLOCK_CHAR * (len(title) + 2) * 3, len(title) + 2, 3)

	t.layer(UI_TEXT_LAYER)
	set_colour(colours.light_yellow)
	t.puts(center, SCREEN_HEIGHT//2-4, title)

	title = 'By Cerepol'
	center = (SCREEN_WIDTH - len(title)) // 2

	t.layer(UI_LAYER)
	set_colour(colours.dark_azure, 150)
	t.puts(center - 1, SCREEN_HEIGHT - 3, BLOCK_CHAR * (len(title) + 2) * 3, len(title) + 2, 3)

	t.layer(UI_TEXT_LAYER)
	set_colour(colours.light_yellow)
	t.puts(center, SCREEN_HEIGHT-2, title)

	t.refresh()
	t.delay(2000)
	t.layer(0)

	while True:
		t.clear()
		set_colour(colours.white, 100)
		t.put(0, 0, 0x5E)
		t.refresh()

		choice = menu('', ['Start a new Adventure', 'Continue Previous game', 'Quit'], 22)

		if choice == 0:
			new_game()
			play_game()	

		elif choice == 1:
			try:
				load_game()
			except:
				msgbox('\n No saved game to load.\n', 24)
				continue
			play_game()
			
		elif choice == 2:
			break

	t.close()

######################
# Init and Main loop #
######################

pixels_w = 12 * SCREEN_WIDTH
pixels_h = 12 * SCREEN_HEIGHT

#ENSURE Save directory exists
if not os.path.isdir(SAVE_PATH):
	os.makedirs(SAVE_PATH)

t.open()
render.t = t

mapsize = str(SCREEN_WIDTH) + "x" + str(SCREEN_HEIGHT)
t.set("window: size=" + mapsize + ", resizeable=true")
t.set("window.title=The Cool Roguelike Project")
t.set("font: ./terminal12x12_gs_ro.png, size=12x12")
t.set("input.filter={keyboard, mouse+}")
t.set("0x5E: cleaving_minotaur.jpg, resize=" + str(pixels_w) + "x" + str(pixels_h))
#t.composition(t.TK_ON)

main_menu()
