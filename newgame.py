"""New Attempt at making a game"""
from abc import ABC, abstractmethod
from bearlibterminal import terminal as t

from constants import *

scene_manager = []


class Scene(ABC):
	"""Abstract Scene"""

	@abstractmethod
	def render(self):
		"""Renderer"""
		pass

	@abstractmethod
	def input(self):
		"""Input Handler"""
		pass

class MainMenuScene(Scene):

	def __init__(self):
		self.splash = True

	def render(self):
		if splash:
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

			splash = False

		



def main():
	"""Setup screen and start main menu"""
	pixels_w = 12 * SCREEN_WIDTH
	pixels_h = 12 * SCREEN_HEIGHT

	#ENSURE Save directory exists
	if not os.path.isdir(SAVE_PATH):
	os.makedirs(SAVE_PATH)

	t.open()

	mapsize = str(SCREEN_WIDTH) + "x" + str(SCREEN_HEIGHT)
	t.set("window: size=" + mapsize + ", resizeable=true")
	t.set("window.title=The Cool Roguelike Project")
	t.set("font: ./terminal12x12_gs_ro.png, size=12x12")
	t.set("input.filter={keyboard, mouse+}")
	t.set("0x5E: cleaving_minotaur.jpg, resize=" + str(pixels_w) + "x" + str(pixels_h))

	mainmenu = MainMenuScene()

	scene_manager.append(mainmenu)

	#while there is a scene to process don't exit
	while scene_manager:



if __name__ == "__main__":
	main()
