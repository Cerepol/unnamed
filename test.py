"""test shit"""
from bearlibterminal import terminal
 
terminal.open()

name = "\u2588" * 25
terminal.layer(0)
terminal.color(terminal.color_from_argb(255, 255, 0, 0))
#terminal.bkcolor("red")
terminal.print(1, 1, name, width=5, height=5)

terminal.layer(10)
terminal.color("green")
terminal.print(1, 2, name, width=5, height=1)

terminal.printf(1, 10, "[color=orange]Welcome[/color][color=red] to the lang zone[/color]")

terminal.refresh()

while terminal.read() != terminal.TK_ESCAPE:
	pass
 
terminal.close()
