"""
A class for identifying a product.

>>> from warehouse.instance.element import context

>>> with context():
...     p1 = Product(None, "tracksuite")
...     p2 = Product(None, "cupboard")

>>> repr(p1)
"Product(key=0, name='tracksuite')"
>>> repr(p2)
"Product(key=1, name='cupboard')"

>>> csv_1 = list(Product.to_csv((p1, p2)))
>>> for row in csv_1:
...     if not str.startswith(row, "#"):
...         print(row)
key;name
0;tracksuite
1;cupboard

>>> with context():
...     for xbin in Product.from_csv(csv_1):
...         print(repr(xbin))
Product(key=0, name='tracksuite')
Product(key=1, name='cupboard')
"""


from warehouse.instance.element import (
    Element,
)


class Product(Element):
    """A class for describing products."""
