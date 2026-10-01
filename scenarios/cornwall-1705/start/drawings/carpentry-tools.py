from engine.draw import Sheet
from parts import carpentry_tools

s = Sheet("carpentry-tools", "Carpenter's tools", "On and around the bench, as they are in the smithy · to scale")
c = s.place(carpentry_tools)
s.label("bow saw", c["bow-saw"], side="left")
s.label("planes: jack and smoother", c["planes"], side="left")
s.label("chisels", c["chisels"])
s.label("hand saw", c["hand-saw"])
s.label("axe", c["axe"], side="left")
s.label("augers (hand drills): holes up to 5 cm across", c["augers"], side="left")
s.label("adze", c["adze"])
s.label("drawknife", c["drawknife"], side="left")
s.label("the bench: they can make benches, frames, simple wooden pumps and troughs", c.at(500, 790))
s.dim(c["bit-left"], c["bit-right"], "5 cm")
s.save()
