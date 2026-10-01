from engine.draw import Sheet
from parts import smith_tools

s = Sheet("smith-tools", "Blacksmith's tools", "On the rack and the vice post, as they hang in the smithy · to scale")
t = s.place(smith_tools)
s.label("hand hammers", t["hammers"], side="left")
s.label("fuller and flatter, for shaping", t["fuller"])
s.label("punches and chisels", t["punches"])
s.label("tongs", t["tongs"], side="left")
s.flaw("files: hand-cut and worn; with patience they can flatten a surface to about 1 mm", t["worn"])
s.label("sledge", t["sledge"], side="left")
s.label("leg vice on its post", t["vice"])
s.label("screw and tommy bar", t["screw"])
s.save()
