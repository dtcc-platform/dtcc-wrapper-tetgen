"""
Public package entry points for dtcc_wrapper_tetgen.
"""

from . import switches
from .adapter import tetrahedralize
from ._tetwrap import TetwrapIO

__all__ = ["tetrahedralize", "TetwrapIO", "switches"]
