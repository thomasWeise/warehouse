"""
A class for identifying a material.

This class here is just a subclass of :class:`~warehouse.instance.named.Named`
that does not add any new attributes or functionality.
If we extend this later, we may need to import the `dataclass` decorator.


>>> m1 = Material(1, "test")
>>> str(m1)
'M1'

>>> repr(m1)
"Material(key=1, name='test')"

>>> m2 = Material(2)
>>> str(m2)
'M2'

>>> repr(m2)
'Material(key=2, name=None)'

>>> csv1 = list(Material.to_csv((m1, m2)))
>>> for txt in csv1[:-3]:
...     print(txt)
key;name
1;test
2
# key: the unique key identifying the object within its type
# name: the name of the object

>>> m3 = Material(3)
>>> str(m3)
'M3'

>>> csv2 = list(Material.to_csv((m3, m2)))
>>> for txt in csv2[:-3]:
...     print(txt)
key
2
3
# key: the unique key identifying the object within its type

>>> for obj in Material.from_csv(csv1):
...     print(repr(obj))
Material(key=1, name='test')
Material(key=2, name=None)

>>> for obj in Material.from_csv(csv2):
...     print(repr(obj))
Material(key=2, name=None)
Material(key=3, name=None)
"""

from warehouse.instance.named import Named


class Material(Named):
    """A class for identifying a material."""
