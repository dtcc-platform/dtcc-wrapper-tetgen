"""Wrapper around the pybind11 TetwrapIO with marker normalization helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from . import _tetwrap


@dataclass(slots=True)
class TetwrapIO:
    """Lightweight wrapper that keeps TetGen output arrays zero-copy and normalizes markers."""

    _io: _tetwrap.TetwrapIO
    interior_default: Optional[int] = -10
    normalize_on_init: bool = True
    _normalized: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.normalize_on_init:
            self.normalize_markers()

    def normalize_markers(self, *, force: bool = False) -> None:
        """Normalize face markers in place, undoing offsets and remapping 0 to the default."""
        if self._normalized and not force:
            return
        self._normalize_marker_array(self._io.boundary_tri_markers)
        self._normalize_marker_array(self._io.tri_markers)
        object.__setattr__(self, "_normalized", True)

    def _normalize_marker_array(self, markers: Any) -> None:
        if markers is None:
            return
        arr = np.asarray(markers)
        if arr.size == 0:
            return
        if self.interior_default is not None:
            arr[arr == 0] = self.interior_default
        np.subtract(arr, 1, out=arr, where=arr > 0)

    def raw(self) -> _tetwrap.TetwrapIO:
        """Return the underlying pybind11 object."""
        return self._io

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - passthrough
        return getattr(self._io, name)


__all__ = ["TetwrapIO"]
