# dtcc-wrapper-tetgen

Lightweight wheels and sdists for the TetGen volume-meshing kernel plus a small Python adapter. The package exposes

- `tetrahedralize(...)`: run TetGen on a watertight surface mesh and return volumetric elements or the richer `TetwrapIO`.
- `switches.build_tetgen_switches(...)`: compose TetGen switch strings from descriptive keyword arguments.
- `TetwrapIO`: container returned by `_tetwrap.tetrahedralize` with NumPy arrays for vertices, tetrahedra, faces, edges, etc.

## Repository layout

```
src/dtcc_wrapper_tetgen/
  adapter.py              # Python helper around the pybind11 module
  switches.py             # switch builder that mirrors TetGen CLI options
  _tetwrap.*              # compiled extension (built during pip install)
  cpp/
    tetrap                # (build products when you configure locally)
    tetwrap/tetwrap.cpp   # pybind11 bindings
    tetgen/               # vendored TetGen sources (tetgen.cxx, predicates.cxx,…)
scripts/
  vendor_tetgen.sh        # convenience helper to refresh TetGen sources
demos/
  demo.py                 # small example on a box PLC
```

> **Note:** Wheels require the TetGen sources to be checked in. Populate `src/dtcc_wrapper_tetgen/cpp/tetgen` before building or installing.

## Prerequisites

- Python 3.9+
- C++17 toolchain
- CMake ≥ 3.18
- `pip install scikit-build-core pybind11 numpy` if you plan to build locally

## Vendor TetGen sources (must happen before `pip install .`)

Vendoring downloads TetGen to the package’s `_deps` directory. Run:

```bash
cd dtcc-wrapper-tetgen
bash vendor_tetgen.sh           # defaults to v1.5.0
# or choose another tag:
TETGEN_VERSION=v1.6.0 ./scripts/vendor_tetgen.sh
```

The script syncs `src/dtcc_wrapper_tetgen/cpp/tetgen`. Commit the updated files so sdists and wheels contain the sources.

## Install

```bash
python -m venv .venv && source .venv/bin/activate  # optional
pip install --upgrade pip
pip install .                                      # builds _tetwrap inplace
# Development mode:
pip install -e .
```

`pip install` automatically builds `_tetwrap` via `scikit-build-core` and CMake, placing the extension alongside the Python sources.

## Generating a volume mesh

The adapter targets manifold triangle surfaces (PLC input). You can either request the rich `TetwrapIO` or just get points/tets:

```python
import numpy as np
from dtcc_wrapper_tetgen import switches, tetrahedralize, TetwrapIO

# Cube vertices/faces (0-based indices defining a watertight surface).
vertices = np.array([
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [1.0, 0.0, 1.0],
    [1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0],
], dtype=float)

faces = np.array([
    [0, 1, 2], [0, 2, 3],  # bottom
    [4, 5, 6], [4, 6, 7],  # top
    [0, 1, 5], [0, 5, 4],  # south
    [1, 2, 6], [1, 6, 5],  # east
    [2, 3, 7], [2, 7, 6],  # north
    [3, 0, 4], [3, 4, 7],  # west
], dtype=int)

# Boundary facets: polygons describing each face loop.
boundary_facets = {
    "south": [0, 1, 5, 4],
    "east": [1, 2, 6, 5],
    "north": [2, 3, 7, 6],
    "west": [3, 0, 4, 7],
    "top": [4, 5, 6, 7],
    "bottom": [0, 1, 2, 3],
}

switch_str = switches.build_tetgen_switches(
    params={
        "plc": True,
        "quality": 1.6,         # triangle quality (radius-edge ratio)
        "max_volume": 0.02,     # enforce target tetra volume
        "output_faces": True,
        "output_neighbors": True,
    }
)

mesh_io: TetwrapIO = tetrahedralize(
    vertices,
    faces,
    boundary_facets,
    switches_overrides={"extra": switch_str},
    return_io=True,
)

points = mesh_io.points          # (N, 3)
tets = mesh_io.tets              # (K, 4)
boundary_triangles = mesh_io.tri_faces
```

For basic `(points, tets)` output set `return_io=False`. Switch toggles are described in `switches.py`.

## Building the extension manually (optional)

You can build the `_tetwrap` extension without `pip` for local debugging:

```bash
cd src/dtcc_wrapper_tetgen/cpp/tetwrap
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

The resulting `_tetwrap.*.so` is placed in `src/dtcc_wrapper_tetgen`, making `python -m demos.demo` usable with `PYTHONPATH=src`.

