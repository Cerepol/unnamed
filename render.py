"""Animation module"""
from gamemap import is_blocked
from constants import EFFECT_LAYER
from constants import CURSOR_LAYER
from constants import OVERLAY_LAYER
from constants import MAP_WIDTH
from constants import MAP_HEIGHT
from constants import BLOCK_CHAR
import colours

t = None

def draw_max_range(player, max_range):
	"""Draws a dark overlay over anything not in range"""
	
	t.layer(OVERLAY_LAYER)

	if max_range is None:
		t.clear_area(0, 0, MAP_WIDTH, MAP_HEIGHT)
		return

	set_colour(colours.black, 200)

	for x in range(0, MAP_WIDTH):
		for y in range(0, MAP_HEIGHT):
			if player.distance(x, y) > max_range or is_blocked(x, y, None, tilesOnly=True):
				t.put(x, y, BLOCK_CHAR)


def draw_cursor(x, y):
	"""Draws a cursor at the specified point"""

	if x != None:
		t.layer(CURSOR_LAYER)
		t.clear_area(0, 0, MAP_WIDTH, MAP_HEIGHT)
		set_colour(colours.white, 150)
		t.put(x, y, BLOCK_CHAR)
		t.refresh()
	else:
		t.layer(CURSOR_LAYER)
		t.clear_area(0, 0, MAP_WIDTH, MAP_HEIGHT)


def draw_fireball(mx, my):
	"""Draw an expanding/contracting fireball"""
	t.layer(EFFECT_LAYER)

	effected_points = [(mx + dx, my + dy) for (dx, dy) in 
		((-1, -1), (-1, 1), (-1, 0), (0, -1), (0, 0), (0, +1), (+1, 0), (+1, -1), (+1, +1))]

	for (x, y) in effected_points:
		if is_blocked(x, y, None, tilesOnly=True):
			effected_points.remove((x, y))

	set_colour(colours.red)
	for (x, y) in effected_points[4:-4]:
		t.put(x, y, chr(177))
	t.refresh()
	t.delay(50)

	set_colour(colours.orange)
	for (x, y) in effected_points[2:-2]:
		t.put(x, y, chr(177))
	t.refresh()
	t.delay(50)

	set_colour(colours.red)
	for (x, y) in effected_points:
		t.put(x, y, chr(177))
	t.refresh()
	t.delay(50)

	set_colour(colours.orange)
	for (x, y) in effected_points:
		t.put(x, y, chr(177))
	t.refresh()
	t.delay(50)

	set_colour(colours.red)
	for (x, y) in effected_points:
		t.put(x, y, chr(177))
	t.refresh()
	t.delay(100)

	t.clear_area(effected_points[0][0], effected_points[0][1], 
				effected_points[-1][0], effected_points[-1][1])
	set_colour(colours.orange)
	for (x, y) in effected_points[2:-2]:
		t.put(x, y, chr(177))
	t.refresh()
	t.delay(100)


	t.clear_area(effected_points[0][0], effected_points[0][1], 
				effected_points[-1][0], effected_points[-1][1])
	set_colour(colours.dark_red)
	for (x, y) in effected_points[4:-4]:
		t.put(x, y, chr(177))
	t.refresh()
	t.delay(150)

	for point in effected_points:
		t.clear_area(point[0], point[1], 1, 1)
	t.refresh()

	return effected_points

def set_colour(rgb, alpha=255):
	"""Wrapper for bearlibterminal color method, so I can spell properly"""	
	hexcolour = alpha
	hexcolour = hexcolour * 256 + rgb[0]
	hexcolour = hexcolour * 256 + rgb[1]
	hexcolour = hexcolour * 256 + rgb[2]
	t.color(hexcolour)
