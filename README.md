# dtcc-tetgen-wrapper

[![CI](https://github.com/dtcc-platform/dtcc-wrapper-tetgen/actions/workflows/ci.yml/badge.svg)](https://github.com/dtcc-platform/dtcc-wrapper-tetgen/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Lightweight Python wrapper for the TetGen tetrahedral mesh generator. This package provides Python bindings to TetGen's powerful 3D Delaunay tetrahedralization and mesh generation capabilities.

## What is this?

`dtcc-tetgen-wrapper` ships the [TetGen](http://wias-berlin.de/software/tetgen/) 3D tetrahedralization engine as a self-contained Python extension. It exposes a concise, NumPy-friendly API that feeds surface meshes to TetGen and returns tetrahedral cells, boundary metadata, and adjacency information.

**Key Point**: You get TetGen's command-line power with a single function call — no separate binaries or intermediate `.node` / `.ele` files.

## Quick Start

### 1.1 Install through PyPI

```bash
pip install dtcc-tetgen-wrapper
```

### 1.2 Manual Build and Install

1. After cloning this repository, wheels require the TetGen sources to be checked in. Populate `dtcc_wrapper_tetgen/cpp/tetgen` before building or installing.

```bash
git clone https://github.com/dtcc-platform/dtcc-wrapper-tetgen.git
```

2. Vendoring downloads TetGen to the package’s `dtcc_wrapper_tetgen/cpp/` directory. Run:

```bash

cd dtcc-wrapper-tetgen
bash vendor_tetgen.sh           # defaults to v1.5.1
# or choose another tag:
TETGEN_VERSION=v1.6.0 ./vendor_tetgen.sh
```

3. Build and Install

```bash
python -m venv .venv && source .venv/bin/activate  # optional
pip install --upgrade pip
pip install .                                      # builds _tetwrap inplace
```


### 2. Generate a mesh

The adapter targets manifold triangle surfaces (PLC input). You can either request the rich `TetwrapIO` or just get points/tets:

```python
import numpy as np
from dtcc_wrapper_tetgen import switches, tetrahedralize, TetwrapIO

vertices = np.array(
    [
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 1],
        [1, 1, 1],
        [0, 1, 1],
    ],
    dtype=float,
)

faces = np.array(
    [
        [0, 1, 2], [0, 2, 3],
        [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4],
        [1, 2, 6], [1, 6, 5],
        [2, 3, 7], [2, 7, 6],
        [3, 0, 4], [3, 4, 7],
    ],
    dtype=np.int64,
)

boundary_facets = {
    "bottom": [0, 1, 2, 3],
    "top": [4, 5, 6, 7],
    "south": [0, 1, 5, 4],
    "north": [2, 3, 7, 6],
    "east": [1, 2, 6, 5],
    "west": [3, 0, 4, 7],
}

switches = switches.build_tetgen_switches(
    params={
        "plc": True,
        "quality": 1.6,         # triangle quality (radius-edge ratio)
        "max_volume": 0.02,     # enforce target tetra volume
        "output_faces": True,
        "output_neighbors": True,
    }
)

mesh: TetwrapIO = tetrahedralize(
    vertices,
    faces,
    boundary_facets,
    switches_params= switches
    return_io=True,
)

points = mesh.points                # (N, 3)
tets = mesh.tets                    # (K, 4)
boundary_triangles = mesh.tri_faces # (B, 3)
```

For basic `(points, tets)` output set `return_io=False`. Switch toggles are described in `switches.py`.

## Features

- ✅ **High-level mesh API**: Call `tetrahedralize()` with NumPy arrays to obtain tetrahedra, faces, edges, markers, and neighbor connectivity in one shot
- ✅ **Switch builder**: Describe TetGen command-line switches with expressive Python keywords via `switches.build_tetgen_switches()`
- ✅ **Marker normalization**: `TetwrapIO` converts TetGen's 1-based boundary markers into zero-based arrays for Python tooling
- ✅ **Zero-copy arrays**: Access TetGen output buffers without redundant copies or conversions
- ✅ **Quality & sizing controls**: Configure radius-edge ratios, dihedral angles, and per-region volume targets programmatically
- ✅ **Vendored TetGen sources**: Wheels bundle vetted TetGen code; source builds pull it in automatically using `vendor_tetgen.sh`

## Use Cases

- Python workflows that need robust tetrahedral meshes from watertight triangle surfaces
- PDE and FEM solvers that combine Python front-ends with compiled numerical kernels
- Geometry processing pipelines that favor TetGen over CGAL or Gmsh
- Automated meshing backends for CAD, GIS, or simulation services

## Documentation

- [README.md](README.md) — in-depth build, troubleshooting, and development guide
- [demos/demo.py](demos/demo.py) — end-to-end PLC meshing example
- [tests/](tests/) — pytest suite illustrating inputs, outputs, and corner cases
- [vendor_tetgen.sh](vendor_tetgen.sh) — helper script that syncs official TetGen sources for source builds

## APIs

### `tetrahedralize(vertices, faces, boundary_facets, …)`: 
Run TetGen on a Piecewise Linear Complex (PLC) and return a `TetwrapIO` wrapper or raw arrays.

```python
def tetrahedralize(
    V: np.ndarray,
    F: Optional[np.ndarray] = None,
    boundary_facets: Optional[Dict[str, List[List[int]]]] = None,
    *,
    return_io: bool = False,
    return_faces: bool = False,
    return_edges: bool = False,
    return_neighbors: bool = False,
    return_boundary: bool = False,
    interior_default: int = -10,
    tetgen_switches: Optional[str] = None,
    **kwargs
) -> Union[Tuple[np.ndarray, ...], TetwrapIO]
```

**Parameters:**
- `V`: (N, 3) array of vertex coordinates
- `F`: Optional (M, 3) or (M, 4) array of face indices
- `boundary_facets`: Dictionary mapping boundary names to face lists
- `return_io`: If True, return TetwrapIO object instead of tuple
- `return_faces/edges/neighbors/boundary`: Control which outputs to include
- `interior_default`: Marker value for interior (non-boundary) faces
- `tetgen_switches`: Raw TetGen switch string (overrides kwargs)
- `**kwargs`: TetGen parameters (quality, max_volume, etc.)


- **`TetwrapIO`**: Lightweight accessor exposing `points`, `tets`, `tri_faces`, `boundary_tri_faces`, `neighbors`, `edges`, and marker normalization helpers.
- **`switches.build_tetgen_switches(params, **overrides)`**: Compose TetGen command-line switches from descriptive Python parameters.

```python
from dtcc_wrapper_tetgen import switches, tetrahedralize, TetwrapIO

params = switches.tetgen_defaults()
params.update({"quality": (1.8, 20), "max_volume": 10.0, "output_faces": True})
switch_str = switches.build_tetgen_switches(params=params, quiet=True)
```

## Requirements

- **For installation**
  - Python 3.9 or newer
  - pip with wheel support
  - NumPy (installed automatically as a dependency)
- **For building from source**
  - C++17 compiler toolchain
  - CMake ≥ 3.18 and `scikit-build-core`
  - `pybind11`, `numpy`, and `pytest` for local builds and tests
  - Run `bash vendor_tetgen.sh` to fetch TetGen sources before `pip install .`


## Troubleshooting

### Common Issues

**ImportError: No module named '_tetwrap'**
- Ensure TetGen sources are vendored: `bash vendor_tetgen.sh`
- Rebuild the package: `pip install --force-reinstall .`

**Segmentation fault during tetrahedralization**
- Check that input vertices form a valid 3D geometry (not coplanar)
- Ensure faces define a closed, watertight surface
- Verify face indices are within bounds

**Poor mesh quality**
- Adjust quality parameters: decrease `max_radius_edge_ratio`, increase `min_dihedral_angle`
- Use smaller `max_volume` for finer meshes
- Enable quality mode with `quality=True`

**TetGen fails with invalid input**
- Verify input is a valid Piecewise Linear Complex (PLC)
- Check for self-intersecting faces
- Ensure consistent face orientation (outward normals)

## Performance Tips

1. **Large meshes**: Use `quiet=True` to reduce console output overhead
2. **Quality vs. Speed**: Balance quality constraints with mesh size requirements
3. **Memory usage**: Return only needed components (avoid `return_io=True` if you only need points/tets)
4. **Parallel processing**: TetGen itself is single-threaded; parallelize at the Python level for multiple meshes

## Contributing

Contributions welcome! Open an issue or pull request, run the test suite & code quality checks, and document how to reproduce your changes.

## License

This wrapper is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0), matching TetGen's license. See [LICENSE](LICENSE) for details.

**Important**: TetGen itself is also AGPL-licensed. Any software using this wrapper must comply with AGPL terms, including providing source code for network services.

## Acknowledgements

- TetGen is developed by Hang Si and distributed under the AGPL license.
- Part of the [DTCC Platform](https://github.com/dtcc-platform), which advances open tooling for digital twins of cities.

## Links

- [GitHub Repository](https://github.com/dtcc-platform/dtcc-wrapper-tetgen)
- [Issue Tracker](https://github.com/dtcc-platform/dtcc-wrapper-tetgen/issues)
- [TetGen Manual](https://codeberg.org/TetGen/Manuals/src/branch/main/tetgen-manual-1.5.pdf)
- [DTCC Platform](https://github.com/dtcc-platform)
