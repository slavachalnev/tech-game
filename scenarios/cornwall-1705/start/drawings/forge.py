from engine.draw import Sheet
from parts import forge

s = Sheet("forge", "Hearth and bellows", "Front view, the fire pit cut open · to scale")
f = s.place(forge)
s.label("rocking lever", f["lever"])
s.flaw("needs a second person (or a boy) on this handle whenever the smith works", f["handle"])
s.label("leather and ash-wood bellows", f["bellows"])
s.label("cast-iron nozzle (tuyere)", f["tuyere"])
s.label("welding heat, about 1300 °C, in a fist-sized spot at the nozzle", f["heat"])
s.label("fire pit, 15 cm deep, for coal or charcoal", f["pit"])
s.flaw("can't melt iron in any quantity; a crucible melts a few kg of brass, bronze or lead", f["fire"])
s.label("brick and stone hearth, 1.2 by 0.9 m", f["hearth"])
s.dim(f.at(-1565, 0), f.at(-60, 0), "bellows 1.5 m")
s.dim(f.at(0, 0), f.at(1200, 0), "1.2 m")
s.save()
