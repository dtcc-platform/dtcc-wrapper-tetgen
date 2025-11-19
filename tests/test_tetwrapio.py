"""Tests for the TetwrapIO helper class."""

from __future__ import annotations

import numpy as np

from dtcc_tetgen_wrapper.tetwrapio import TetwrapIO


class _FakeRawIO:
    def __init__(self) -> None:
        self.boundary_tri_markers = np.array([0, 2], dtype=np.int32)
        self.tri_markers = np.array([1, 0], dtype=np.int32)
        self.points = np.empty((0, 3))
        self.tets = np.empty((0, 4), dtype=np.int32)


def test_normalize_markers_updates_arrays() -> None:
    """Markers are normalized on initialization by default."""
    raw = _FakeRawIO()
    TetwrapIO(raw, interior_default=-1)

    # 0 -> -1, positives are decremented.
    assert raw.boundary_tri_markers.tolist() == [-1, 1]
    assert raw.tri_markers.tolist() == [0, -1]


def test_raw_passthrough() -> None:
    """The raw() helper returns the wrapped pybind object."""
    raw = _FakeRawIO()
    wrapper = TetwrapIO(raw, normalize_on_init=False)
    assert wrapper.raw() is raw
