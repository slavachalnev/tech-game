from engine.draw import Sheet
from parts import drawing_kit

s = Sheet("drawing-kit", "Drawing instruments", "As kept on the smithy wall · to scale")
d = s.place(drawing_kit)
s.label("paper", d["paper"], side="left")
s.label("60 cm brass ruler, marked in millimeters", d["marks"], side="left")
s.label("ink", d["ink"])
s.label("quill pens", d["quills"])
s.label("dividers", d["dividers"])
s.dim(d.at(-60, -110), d.at(540, -110), "60 cm")
s.save()
