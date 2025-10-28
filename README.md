# dtcc-wrapper-tetgen

[![CI](https://github.com/dtcc-platform/dtcc-wrapper-tetgen/actions/workflows/ci.yml/badge.svg)](https://github.com/dtcc-platform/dtcc-wrapper-tetgen/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Lightweight Python wrapper for the TetGen tetrahedral mesh generator. This package provides Python bindings to TetGen's powerful 3D Delaunay tetrahedralization and mesh generation capabilities.

## Features

- **Simple Python API**: Easy-to-use interface for tetrahedral mesh generation
- **NumPy Integration**: Direct conversion between TetGen data structures and NumPy arrays
- **Flexible Mesh Control**: Support for quality constraints, volume constraints, and boundary preservation
- **Comprehensive Switch Builder**: Pythonic interface for TetGen's command-line switches
- **Type Hints**: Full type annotations for better IDE support and type checking
- **Cross-platform**: Works on Linux, macOS, and Windows (with appropriate compiler)

## Key Components

- `tetrahedralize(...)`: Generate tetrahedral meshes from surface meshes
- `build_tetgen_switches(...)`: Build TetGen command strings using descriptive parameters
- `TetwrapIO`: Rich container for mesh data with NumPy arrays

## Repository layout

```
dtcc_wrapper_tetgen/
  adapter.py              # Python helper around the pybind11 module
  switches.py             # switch builder that mirrors TetGen CLI options
  tetwrapio.py            # Python-side wrapper for the pybind result
  cpp/
    tetwrap/tetwrap.cpp   # pybind11 bindings
    tetgen/               # vendored TetGen sources (tetgen.cxx, predicates.cxx,…)
vendor_tetgen.sh          # convenience helper to refresh TetGen sources
demos/
  demo.py                 # small example on a box PLC
```

> **Note:** Wheels require the TetGen sources to be checked in. Populate `dtcc_wrapper_tetgen/cpp/tetgen` before building or installing.

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

The script syncs `dtcc_wrapper_tetgen/cpp/tetgen`. Commit the updated files so sdists and wheels contain the sources.

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
cd dtcc_wrapper_tetgen/cpp/tetwrap
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

The resulting `_tetwrap.*.so` is placed in `dtcc_wrapper_tetgen`, making `python -m demos.demo` usable with `PYTHONPATH=.`

## Quick Start

```python
import numpy as np
from dtcc_wrapper_tetgen import tetrahedralize

# Define a simple tetrahedron
vertices = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
], dtype=np.float64)

# Generate tetrahedral mesh
points, tets = tetrahedralize(vertices)
print(f"Generated {len(tets)} tetrahedra from {len(points)} points")
```

## API Reference

### tetrahedralize()

Main function for generating tetrahedral meshes.

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

### build_tetgen_switches()

Build TetGen command-line switches from descriptive parameters.

```python
switches = build_tetgen_switches(
    quality=True,              # Enable quality meshing
    max_radius_edge_ratio=1.5, # Maximum radius-edge ratio
    min_dihedral_angle=15,     # Minimum dihedral angle
    max_volume=0.1,            # Maximum tetrahedron volume
    verbose=True               # Enable verbose output
)
```

### Common TetGen Parameters

| Parameter | Switch | Description |
|-----------|--------|-------------|
| `quality` | `-q` | Enable quality mesh generation |
| `max_radius_edge_ratio` | `-q{val}` | Maximum radius-edge ratio bound |
| `min_dihedral_angle` | `-q{val}/` | Minimum dihedral angle bound |
| `max_volume` | `-a{val}` | Maximum tetrahedron volume |
| `max_steiner_points` | `-S{num}` | Maximum number of Steiner points |
| `quiet` | `-Q` | Suppress console output |
| `verbose` | `-V` | Verbose output |
| `face_output` | `-f` | Output faces |
| `edge_output` | `-e` | Output edges |
| `neighbor_output` | `-n` | Output neighbors |

## Advanced Examples

### Quality Mesh with Volume Control

```python
from dtcc_wrapper_tetgen import tetrahedralize, build_tetgen_switches

# Create a cube
vertices = np.array([
    [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
    [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
], dtype=np.float64)

# Define faces with boundary markers
boundary_facets = {
    "bottom": [[0, 3, 2, 1]],
    "top": [[4, 5, 6, 7]],
    "sides": [[0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
}

# Generate high-quality mesh
result = tetrahedralize(
    vertices,
    boundary_facets=boundary_facets,
    quality=True,
    max_radius_edge_ratio=1.2,
    min_dihedral_angle=20,
    max_volume=0.01,
    return_io=True
)

print(f"Mesh quality statistics:")
print(f"  Vertices: {result.points.shape[0]}")
print(f"  Tetrahedra: {result.tets.shape[0]}")
print(f"  Surface faces: {result.tri_faces.shape[0] if result.tri_faces is not None else 0}")
```

### Using Face Constraints

```python
# Define a box with holes or internal boundaries
faces = np.array([
    # Outer box faces (triangulated)
    [0, 1, 2], [0, 2, 3],  # bottom
    [4, 5, 6], [4, 6, 7],  # top
    # ... more faces
], dtype=np.int32)

# Mesh with face preservation
mesh_io = tetrahedralize(
    vertices,
    faces=faces,
    plc=True,  # Treat input as Piecewise Linear Complex
    facet_constraints=True,  # Preserve input facets
    return_io=True
)
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=dtcc_wrapper_tetgen --cov-report=html

# Run specific test categories
pytest tests/ -m "not slow"  # Skip slow tests
pytest tests/test_adapter.py  # Run specific test file
```

## Development

### Setting up development environment

```bash
# Clone repository
git clone https://github.com/dtcc-platform/dtcc-wrapper-tetgen.git
cd dtcc-wrapper-tetgen

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest mypy black isort pre-commit
pre-commit install
```

### Running code quality checks

```bash
# Format code
black dtcc_wrapper_tetgen tests
isort dtcc_wrapper_tetgen tests

# Type checking
mypy dtcc_wrapper_tetgen

# Run pre-commit hooks
pre-commit run --all-files
```

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

## License

This wrapper is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0), matching TetGen's license. See [LICENSE](LICENSE) for details.

**Important**: TetGen itself is also AGPL-licensed. Any software using this wrapper must comply with AGPL terms, including providing source code for network services.

## Citation

If you use this wrapper in your research, please cite both this wrapper and TetGen:

```bibtex
@software{dtcc-wrapper-tetgen,
  title = {dtcc-wrapper-tetgen: Python wrapper for TetGen},
  author = {DTCC Platform Contributors},
  url = {https://github.com/dtcc-platform/dtcc-wrapper-tetgen},
  year = {2024}
}

@article{si2015tetgen,
  title = {TetGen, a Delaunay-based quality tetrahedral mesh generator},
  author = {Si, Hang},
  journal = {ACM Transactions on Mathematical Software},
  volume = {41},
  number = {2},
  pages = {1--36},
  year = {2015}
}
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and code quality checks
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Links

- [TetGen homepage](http://wias-berlin.de/software/tetgen/)
- [TetGen documentation](http://wias-berlin.de/software/tetgen/1.5/doc/manual/)
- [Issue tracker](https://github.com/dtcc-platform/dtcc-wrapper-tetgen/issues)
- [DTCC Platform](https://github.com/dtcc-platform)
