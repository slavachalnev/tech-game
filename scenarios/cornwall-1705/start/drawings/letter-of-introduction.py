from engine.draw import Sheet
from parts import letter

s = Sheet("letter-of-introduction", "Letter of introduction", "Both sides of the folded letter · to scale")
a = s.place(letter, side="address")
b = s.place(letter, at=(200, 0), side="seal")
s.label("the address side", a["address"], side="left")
s.label("wax seal, unbroken", b["seal"])
s.label("folded and sealed, no envelope", b["fold"])
s.note("From", "A Truro lawyer who owes you a favor wrote and sealed it.")
s.dim(b.at(0, 0), b.at(160, 0), "16 cm")
s.save()
