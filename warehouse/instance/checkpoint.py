"""
A class for identifying a checkpoint.

>>> from warehouse.instance.element import context

>>> with context():
...     p1 = Checkpoint(None, "M1")
...     p2 = Checkpoint(None, "S2")

>>> repr(p1)
"Checkpoint(key=0, name='M1')"
>>> repr(p2)
"Checkpoint(key=1, name='S2')"

>>> csv_1 = list(Checkpoint.to_csv((p1, p2)))
>>> for row in csv_1:
...     if not str.startswith(row, "#"):
...         print(row)
key;name
0;M1
1;S2

>>> with context():
...     for xbin in Checkpoint.from_csv(csv_1):
...         print(repr(xbin))
Checkpoint(key=0, name='M1')
Checkpoint(key=1, name='S2')
"""

from typing import Final

from warehouse.instance.element import (
    Element,
)

#: the CSV column for checkpoints
COLUMN_CHECKPOINT: Final[str] = "checkpoint"


class Checkpoint(Element):
    """A class for describing checkpoints."""
