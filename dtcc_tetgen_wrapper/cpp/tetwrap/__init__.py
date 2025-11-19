from . import switches
from ._tetwrap import _tetrahedralize  # returns TetwrapIO
from ._tetwrap import build_volume_mesh  # returns (points, tets)
from ._tetwrap import (
    TetwrapIO,
)

# Convenience alias
tetrahedralize = _tetrahedralize

__all__ = [
    "build_volume_mesh",
    "TetwrapIO",
    "tetrahedralize",
    "switches",
]
