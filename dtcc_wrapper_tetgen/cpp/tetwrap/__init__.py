from ._tetwrap import (
    build_volume_mesh,      # returns (points, tets)
    _tetrahedralize,         # returns TetwrapIO
    TetwrapIO,
)
from . import switches

# Convenience alias
tetrahedralize = _tetrahedralize

__all__ = [
    "build_volume_mesh",
    "TetwrapIO",
    "tetrahedralize",
    "switches",
]
