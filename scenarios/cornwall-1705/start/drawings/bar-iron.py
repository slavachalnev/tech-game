from engine.draw import Sheet
from parts import bar_iron

s = Sheet("bar-iron", "Bar iron", "The bundle from the side · to scale", size=(1600, 520))
b = s.place(bar_iron)
s.label("seven wrought-iron flat bars, 38 by 13 mm, 100 kg in all, from a Bristol merchant", b["left"])
s.label("bound with wire", b["wire"])
s.flaw("streaks of slag along the grain: ordinary merchant bar", b["slag"])
s.dim(b.at(-1850, 0), b.at(1850, 0), "3.7 m", offset=30)
s.save()
