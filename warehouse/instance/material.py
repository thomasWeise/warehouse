"""
A class for identifying a material.

This class here is just a subclass of
:class:`~warehouse.instance.element.Element`
that does not add any new attributes or functionality.
If we extend this later, we may need to import the `dataclass` decorator.

>>> from warehouse.instance.element import context

>>> with context():
...     m1 = Material(None, "Shoe")
...     m2 = Material(1, "Hat")
...     m3 = Material(2, "Skirt")

>>> str(m1)
'M0'
>>> str(m2)
'M1'
>>> str(m3)
'M2'

>>> repr(m1)
"Material(key=0, name='Shoe')"
>>> repr(m2)
"Material(key=1, name='Hat')"
>>> repr(m3)
"Material(key=2, name='Skirt')"

>>> csv1 = list(Material.to_csv((m1, m2, m3)))
>>> for txt in csv1[:-3]:
...     print(txt)
key;name
0;Shoe
1;Hat
2;Skirt
# key: the unique key of the element within its type
# name: the unique name of the element (unique over all elements of all types)

>>> for mat in Material.from_csv(["name", "hello", "world", "material"]):
...     print(repr(mat))
Material(key=0, name='hello')
Material(key=1, name='world')
Material(key=2, name='material')
"""

from warehouse.instance.element import Element


class Material(Element):
    """A class for identifying a material."""
