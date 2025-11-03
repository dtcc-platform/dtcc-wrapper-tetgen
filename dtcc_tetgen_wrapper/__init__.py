"""
Public package entry points for dtcc_tetgen_wrapper.
"""

from . import switches
from .adapter import tetrahedralize
from .tetwrapio import TetwrapIO

__all__ = ["tetrahedralize", "TetwrapIO", "switches"]
