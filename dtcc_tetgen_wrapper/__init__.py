"""
Public package entry points for dtcc_tetgen_wrapper.
"""


from .switches import build_tetgen_switches,tetgen_defaults
from .adapter import tetrahedralize
from .tetwrapio import TetwrapIO

__all__ = ["tetrahedralize", 
           "TetwrapIO", 
           "switches",
           "tetgen_defaults", 
           "build_tetgen_switches"]
