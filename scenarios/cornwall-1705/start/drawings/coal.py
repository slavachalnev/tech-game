from engine.draw import Sheet
from parts import coal

s = Sheet("coal", "Coal", "The heap in its bay, from the front · to scale")
c = s.place(coal)
s.label("Welsh coal, 500 kg, shipped to Portreath and carted up", c["heap"], side="left")
s.label("shovel", c["shovel"])
s.label("bay of boards against the wall", c["bay"])
s.dim(c.at(-400, 0), c.at(400, 0), "80 cm")
s.save()
