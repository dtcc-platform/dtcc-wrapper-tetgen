#!/usr/bin/env python3
"""
Pure adapter for TetGen via the local pybind11 module `_tetwrap`.

Inputs are plain NumPy arrays and Python lists — no dtcc dependency.
"""
from __future__ import annotations

from typing import Iterable, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

# Local binding + helpers (no dtcc here)
from . import _tetwrap
from . import switches
from ._tetwrap import TetwrapIO

BoundaryFacets = Union[
    Sequence[Sequence[int]],                 # list of polygons (each polygon = list of vertex indices)
    Mapping[str, Sequence[int]],             # dict of named polygons: {'south': [...], 'east': [...], ...}
]


def _ensure_ndarray(vertices: np.ndarray, faces: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    V = np.asarray(vertices, dtype=float)
    F = np.asarray(faces, dtype=np.int64)

    if V.ndim != 2 or V.shape[1] != 3:
        raise ValueError("vertices must be (N, 3) float array")
    if F.ndim != 2 or F.shape[1] != 3:
        raise ValueError("faces must be (M, 3) int array of triangles")
    return V, F


def _normalize_boundary_facets(
    boundary_facets: BoundaryFacets,
) -> List[List[int]]:
    if boundary_facets is None:
        raise ValueError("boundary_facets is required (list of polygons or dict of named polygons)")

    if isinstance(boundary_facets, Mapping):
        # Preserve a conventional order if present; then append any extras in key order
        # order = ["south", "east", "north", "west", "top"]
        order = ["top", "north", "east", "south", "west"]
        
        out: List[List[int]] = []
        for key in order:
            if key in boundary_facets:
                poly = list(map(int, boundary_facets[key]))
                if len(poly) < 3:
                    raise ValueError(f"boundary facet '{key}' must have at least 3 vertices")
                out.append(poly)
        # Add any remaining polygons not covered above
        for key in sorted(boundary_facets.keys()):
            if key not in order:
                poly = list(map(int, boundary_facets[key]))
                if len(poly) < 3:
                    raise ValueError(f"boundary facet '{key}' must have at least 3 vertices")
                out.append(poly)
        if len(out) < 5:
            # Not strictly necessary for TetGen, but matches the expectation of 'box-like' domains
            raise ValueError("boundary_facets dict should include at least five polygons (e.g., south,east,north,west,top)")
        return out

    # Assume sequence of sequences
    out = []
    for i, poly in enumerate(boundary_facets):
        p = list(map(int, poly))
        if len(p) < 3:
            raise ValueError(f"boundary facet {i} must have at least 3 vertices")
        out.append(p)
    if len(out) < 1:
        raise ValueError("boundary_facets must contain at least one polygon")
    return out

def tetrahedralize(
    vertices: np.ndarray,
    faces: np.ndarray,
    boundary_facets: BoundaryFacets,
    *,
    face_markers: Optional[Sequence[int]] = None,
    switches_params: Optional[dict] = None,
    switches_overrides: Optional[dict] = None,
    return_io: bool = True,
    return_faces: bool = False,
    return_boundary_faces: bool = False,
    return_edges: bool = False,
    return_neighbors: bool = False,
) -> Union[_TetwrapIO, Tuple[np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]]:
    """
    Run TetGen on a PLC defined by `faces` (triangles) + `boundary_facets` (polygons).

    Parameters
    -----------
    - vertices: (N,3) float array of XYZ coordinates
    - faces: (M,3) int array of triangle indices (0-based)
    - boundary_facets: list of polygon index lists OR dict of named polygons
    - switches_params: tetgen switch parameters (see tetwrap/switches.py)
    - switches_overrides: final overrides for switches
    Notes
    -----
    - Boundary facets are required by TetGen to define the outer boundary of the volume. Tetgen 
      needs a manifold closed surface, so at least one polygon is required and it does not close 
      the volume automatically.

    - Markers are integers assigned to boundary facets in a specific order with:
        - Domain top (highest Z) -> marker -2
        - Domain sides (in order north, east, south, west) -> markers -3, -4, -5, -6
    - Markers on faces of the input mesh carry over to the output tetrahedral mesh boundary face markers.

    Returns
    - points: (Nout,3) float array
    - tets: (K,4 or 10) int array of tetrahedra
    - tri_faces: optional (F,3) boundary triangle list from TetGen `-f`
    - edges: optional (E,2) edge connectivity from TetGen `-e`
    - neighbors: optional (K,4) neighbor indices from TetGen `-n`
    - boundary_tri_faces: optional (BF,3) faces on exterior boundary
    - boundary_tri_markers: optional (BF,) integer markers aligned with `boundary_tri_faces`
    """
    V, F = _ensure_ndarray(vertices, faces)
    B = _normalize_boundary_facets(boundary_facets)
    F_markers = None
    if face_markers is not None:
        F_markers = np.asarray(face_markers, dtype=np.int32)
        if F_markers.ndim != 1:
            raise ValueError("face_markers must be a 1D sequence of integers")
        if F_markers.shape[0] != F.shape[0]:
            raise ValueError("face_markers must have the same length as faces")

    # Build TetGen switches string
    s_params = dict(switches_params or {})
    # Request extras via switches
    if return_faces or return_boundary_faces:
        s_params["output_faces"] = True   # -f
    if return_edges:
        s_params["output_edges"] = True   # -e
    if return_neighbors or return_boundary_faces:
        s_params["output_neighbors"] = True  # -n
    s_over = switches_overrides or {}
    switch_str = switches.build_tetgen_switches(params=s_params, **s_over)

    # Call the C++ extension (rich result)
    io: TetwrapIO = _tetwrap._tetrahedralize(V, F, F_markers, B, switch_str, return_boundary_faces)
    

    if return_io: 
        return io

    # Back-compat/basic tuple return
    points = np.asarray(io.points)
    tets = np.asarray(io.tets)
    tri_faces = None if io.tri_faces is None or isinstance(io.tri_faces, type(None)) else np.asarray(io.tri_faces)
    boundary_tri_faces = (
        None
        if io.boundary_tri_faces is None or isinstance(io.boundary_tri_faces, type(None))
        else np.asarray(io.boundary_tri_faces)
    )
    boundary_tri_markers = (
        None
        if io.boundary_tri_markers is None or isinstance(io.boundary_tri_markers, type(None))
        else np.asarray(io.boundary_tri_markers)
    )
    edges = None if io.edges is None or isinstance(io.edges, type(None)) else np.asarray(io.edges)
    neighbors = None if io.neighbors is None or isinstance(io.neighbors, type(None)) else np.asarray(io.neighbors)
    return points, tets, tri_faces, edges, neighbors, boundary_tri_faces, boundary_tri_markers


__all__ = [
    "tetrahedralize",
    "TetwrapIO",
]
