#!/usr/bin/env python3
"""
Minimal, no-dtcc demo of the TetGen adapter.

Builds a simple rectangular box domain above a unit square ground, then tetrahedralizes it.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

from adapter_tetgen import tetrahedralize
from tetwrap import switches as tet_switches  # type: ignore


def make_unit_box(bottom_size: float = 1.0, height: float = 1.0):
    """
    Create a square base (two triangles) and a 4-wall + top box PLC.
    Returns (vertices, faces, boundary_facets).
    """
    L = float(bottom_size)
    H = float(height)

    # Base square on z=0: (0,0), (L,0), (L,L), (0,L)
    V = [
        [0.0, 0.0, 0.0],  # 0
        [L,   0.0, 0.0],  # 1
        [L,   L,   0.0],  # 2
        [0.0, L,   0.0],  # 3
    ]

    # Triangulate base
    F = [
        [0, 1, 2],
        [0, 2, 3],
    ]

    # Add top corners
    V += [
        [0.0, 0.0, H],  # 4 = t_sw
        [0.0, L,   H],  # 5 = t_nw
        [L,   0.0, H],  # 6 = t_se
        [L,   L,   H],  # 7 = t_ne
    ]

    # Boundary polygons (walls + top) with outward normals
    boundary = {
        # y = 0, outward -y (as seen from -y): [ground west->east, then top east->west]
        "south": [0, 1, 6, 4],
        # x = L, outward +x (as seen from +x): [ground south->north, then top north->south]
        "east":  [1, 2, 7, 6],
        # y = L, outward +y (as seen from +y): [ground east->west, then top west->east]
        "north": [2, 3, 5, 7],
        # x = 0, outward -x (as seen from -x): [ground north->south, then top south->north]
        "west":  [3, 0, 4, 5],
        # top cap CCW as seen from +z
        "top":   [4, 6, 7, 5],
    }

    return np.asarray(V, dtype=float), np.asarray(F, dtype=np.int64), boundary


def main():
    V, F, B = make_unit_box(bottom_size=1.0, height=1.0)

    # Reasonable defaults: PLC + refine and a modest volume limit for a tiny demo
    switches_params = {
        "plc": True,
        # You can try a quality tuple like (ratio, min_dihedral): e.g., (1.5, 20.0)
        # "quality": True,
        "max_volume": 0.05,
        "quiet": True,
        "zero_numbering": True,
    }

    tetwrap_out = tetrahedralize(V, F, B,
                                  return_faces=True,
                                  return_boundary_faces=True,
                                  return_neighbors=True,
                                  switches_params=switches_params)

    print(f"TetGen produced: {len(tetwrap_out.points)} vertices, {len(tetwrap_out.tets)} tets")
    if tetwrap_out.boundary_tri_faces is not None:
        print(f"               {len(tetwrap_out.boundary_tri_faces)} boundary faces")
    # Optional: export to VTU if meshio is available
    try:
        import meshio  # type: ignore
        from pathlib import Path

        outpath = Path(__file__).with_name("demo_box.vtu")

        cells = [("tetra", tetwrap_out.tets)]
        if tetwrap_out.boundary_tri_faces is not None and len(tetwrap_out.boundary_tri_faces) > 0:
            cells.append(("triangle", tetwrap_out.boundary_tri_faces))

        mesh = meshio.Mesh(points=tetwrap_out.points, cells=cells)
        meshio.write("demo_box_faces.vtu", meshio.Mesh(tetwrap_out.points, [("triangle", tetwrap_out.boundary_tri_faces)]))
        meshio.write(outpath, mesh)
        print(f"Wrote {outpath}")

    except Exception as e:
        print("meshio not installed (or write failed)", e)


if __name__ == "__main__":
    main()

