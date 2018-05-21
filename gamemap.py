"""Classes and Functions important to the GameMap"""
from constants import MAP_HEIGHT
from constants import MAP_WIDTH
Map = []



###################
# Building Blocks #
###################
class Rect:
	"""Basic 2D Rectangle"""	
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h

	def center(self):
		"""Finds the center of the rectangle"""
		center_x = (self.x1 + self.x2) // 2
		center_y = (self.y1 + self.y2) // 2
		return (center_x, center_y)

	def intersect(self, other):
		"""Checks if the other rectangle intersects with this one"""
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and 
										self.y1 <= other.y2 and self.y2 >= other.y1)

class Tile:
	"""Defines a singular Tile for the map"""
	# pylint: disable=too-few-public-methods
	def __init__(self, blocked, block_sight=None):
		self.blocked = blocked

		#No tile starts explored
		self.explored = False

		#Any blocking tile should also block sight
		if block_sight is None: 
			block_sight = blocked
		self.block_sight = block_sight		


#################
# Map Functions #
#################
def create_h_tunnel(x1, x2, y):
	"""Creates a horizontal tunnel between the 2 rooms"""
	global Map
	for x in range(min(x1, x2), max(x1, x2) + 1):
		Map[x][y].blocked = False
		Map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
	"""Creates a vertical tunnel between the 2 rooms"""
	global Map
	for y in range(min(y1, y2), max(y1, y2) + 1):
		Map[x][y].blocked = False
		Map[x][y].block_sight = False

def is_visible_tile(x, y):
	"""Checks if a tile is in player FOV"""
	global Map
 
	if x >= MAP_WIDTH or x < 0:
		return False
	elif y >= MAP_HEIGHT or y < 0:
		return False
	elif Map[x][y].blocked:
		return False
	elif Map[x][y].block_sight:
		return False
	return True

def is_blocked(x, y, objects, tilesOnly=False):
	"""Returns if the tile location is blocked"""
	if Map[x][y].blocked:
		return True

	if tilesOnly:
		return False

	for obj in objects:
		if obj.blocks and obj.x == x and obj.y == y:
			return True

	return False

def is_explored(x, y):
	"""Returns if the tile location has been explored"""
	if Map[x][y].explored:
		return True

	return False

def create_room(room):
	"""Attempts to create a room"""
	global Map
	for x in range(room.x1 + 1, room.x2):
		for y in range(room.y1 + 1, room.y2):
			Map[x][y].blocked = False
			Map[x][y].block_sight = False

