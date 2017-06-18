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

x = 10
y = 12
effected_points = [(x + dx, y + dy) for (dx, dy) in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, +1), (+1, -1), (+1, 0), (+1, +1))]
print (effected_points)
print(str(effected_points[0][0]) + " " + str(effected_points[0][1]))
print(effected_points[-1])



terminal.layer(20)

terminal.color("purple")
terminal.put(x, y, '*')

terminal.color("orange")
for (x, y) in effected_points:
	terminal.put(x, y, "*")

terminal.refresh()

while terminal.read() != terminal.TK_ESCAPE:
	pass
 
terminal.close()

