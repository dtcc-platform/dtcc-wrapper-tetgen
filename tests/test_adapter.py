"""Targeted tests for the public tetrahedralize adapter."""

from __future__ import annotations

import numpy as np
import pytest

from dtcc_tetgen_wrapper import adapter
from dtcc_tetgen_wrapper.tetwrapio import TetwrapIO


class _DummyTetwrapResult:
    """Minimal stand-in for the pybind TetGen result."""

    def __init__(self) -> None:
        self.points = np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        self.tets = np.array([[0, 1, 2, 3]], dtype=np.int32)
        self.tri_faces = np.array([[0, 1, 2]], dtype=np.int32)
        self.boundary_tri_faces = np.array([[0, 2, 3]], dtype=np.int32)
        self.boundary_tri_markers = np.array([0, 2], dtype=np.int32)
        self.tri_markers = np.array([1, 0], dtype=np.int32)
        self.edges = np.array([[0, 1]], dtype=np.int32)
        self.neighbors = np.array([[0, 0, 0, 0]], dtype=np.int32)


def _vertices() -> np.ndarray:
    return np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def _faces() -> np.ndarray:
    return np.array(
        [
            [0, 1, 2],
            [0, 1, 3],
            [0, 2, 3],
        ],
        dtype=np.int64,
    )


def _boundary() -> list[list[int]]:
    return [[0, 1, 2]]


def test_boundary_facets_are_required() -> None:
    """tetrahedralize rejects a missing boundary description."""
    with pytest.raises(ValueError):
        adapter.tetrahedralize(_vertices(), _faces(), None)  # type: ignore[arg-type]


def test_face_markers_match_face_count() -> None:
    """face_markers must be the same length as the provided faces."""
    with pytest.raises(ValueError, match="same length as faces"):
        adapter.tetrahedralize(_vertices(), _faces(), _boundary(), face_markers=[1])


def test_returns_tetwrap_io_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """When return_io is True (default) a TetwrapIO wrapper is produced."""
    dummy_result = _DummyTetwrapResult()
    captured = {}

    def _fake_tetrahedralize(V, F, F_markers, B, switch_str, ret_boundary):
        captured["vertices"] = V
        captured["faces"] = F
        captured["face_markers"] = F_markers
        captured["boundary"] = B
        captured["switch_str"] = switch_str
        captured["return_boundary_faces"] = ret_boundary
        return dummy_result

    monkeypatch.setattr(adapter._tetwrap, "_tetrahedralize", _fake_tetrahedralize)

    io = adapter.tetrahedralize(
        _vertices(),
        _faces(),
        _boundary(),
        face_markers=[3, 3, 3],
        switches_params={"quality": 2},
    )

    assert isinstance(io, TetwrapIO)
    assert io.raw() is dummy_result

    assert np.allclose(captured["vertices"], _vertices())
    assert captured["faces"].dtype == np.int64
    assert captured["face_markers"].dtype == np.int32
    assert captured["boundary"] == [[0, 1, 2]]
    # Defaults enable PLC (-p) and our quality request adds q2.
    assert "p" in captured["switch_str"]
    assert "q2" in captured["switch_str"]
    assert captured["return_boundary_faces"] is False


def test_requesting_outputs_sets_switches(monkeypatch: pytest.MonkeyPatch) -> None:
    """Requesting faces/edges/neighbors toggles the associated TetGen switches."""
    dummy_result = _DummyTetwrapResult()
    called = {}

    def _fake_tetrahedralize(V, F, F_markers, B, switch_str, ret_boundary):
        called["switch_str"] = switch_str
        called["return_boundary_faces"] = ret_boundary
        return dummy_result

    monkeypatch.setattr(adapter._tetwrap, "_tetrahedralize", _fake_tetrahedralize)

    result = adapter.tetrahedralize(
        _vertices(),
        _faces(),
        {"top": [0, 1, 2]},
        return_io=False,
        return_faces=True,
        return_edges=True,
        return_neighbors=True,
        return_boundary_faces=True,
    )

    assert called["return_boundary_faces"] is True
    for flag in ("f", "e", "n"):
        assert flag in called["switch_str"]

    assert isinstance(result, tuple)
    assert len(result) == 7
    points, tets, tri_faces, edges, neighbors, boundary_faces, boundary_markers = result
    assert isinstance(points, np.ndarray)
    assert isinstance(boundary_markers, np.ndarray)
    # Markers are normalized: 0 -> default (-10), positives are shifted down.
    assert set(boundary_markers.tolist()) == {-10, 1}
