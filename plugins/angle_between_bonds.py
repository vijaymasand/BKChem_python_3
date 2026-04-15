
import math
from singleton_store import Store
from sets import Set
import operator
from functools import reduce


bs = [b for b in App.paper.selected if b.object_type == "bond"]
if not len( bs) == 2:
  Store.log( _("You have to have 2 bonds selected"), message_type="hint")
else:
  b1, b2 = bs
  center = Set( b1.vertices) & Set( b2.vertices)
  if center:
    a11 = center.pop()
    a12 = b1.atom1 == a11 and b1.atom2 or b1.atom1
    a22 = b2.atom1 == a11 and b2.atom2 or b2.atom1
    v1 = (a12.x - a11.x, a12.y - a11.y, a12.z - a11.z)
    v2 = (a22.x - a11.x, a22.y - a11.y, a22.z - a11.z)
    print(v1, v2)
  else:
    v1 = (b1.atom1.x - b1.atom2.x, b1.atom1.y - b1.atom2.y, b1.atom1.z - b1.atom2.z)
    v2 = (b2.atom1.x - b2.atom2.x, b2.atom1.y - b2.atom2.y, b2.atom1.z - b2.atom2.z)

  dot = reduce( operator.add, map( operator.mul, v1, v2))
  dv1 = math.sqrt( reduce( operator.add, map( lambda x: x**2, v1)))
  dv2 = math.sqrt( reduce( operator.add, map( lambda x: x**2, v2)))

  cos_a = dot / dv1 / dv2

  ret = math.acos( cos_a)
  print(cos_a)

  res = "%.2f" % ( 180*ret/math.pi)

  # draw the result
  x = (b1.atom1.x + b1.atom2.x + b2.atom1.x + b2.atom2.x) / 4
  y = (b1.atom1.y + b1.atom2.y + b2.atom1.y + b2.atom2.y) / 4
  App.paper.new_text( x, y, text=res).draw()
  
  Store.log( res)


