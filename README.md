dtcc-wrapper-tetgen
===================

Lightweight Python wrapper around TetGen using a small pybind11 module (`_tetwrap`) and a pure adapter (`adapter_tetgen.py`). No `dtcc` dependency is required.

Contents
- `tetgen/` — TetGen sources (tetgen.cxx, tetgen.h, predicates.cxx, LICENSE)
- `tetwrap/` — pybind11 binding and helpers (CMake build)
- `adapter_tetgen.py` — Pure Python adapter that calls `_tetwrap.build_volume_mesh`
- `demo.py` — Minimal, no-dtcc example that builds a simple box volume mesh

Build
1) Build the pybind11 module `_tetwrap`:

   ```bash
   cd tetwrap
   mkdir -p build && cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   cmake --build . -j
   ```

   The compiled module (`_tetwrap.*.so`/`.pyd`) will be placed in `tetwrap/` so Python can import it.

2) Run the demo:

   ```bash
   cd ..
   python ../demo.py
   ```

Adapter Usage
- Import and call `tetrahedralize(vertices, faces, boundary_facets, switches_params=None, switches_overrides=None)`.
- Returns `(points, tets)` as NumPy arrays.

Notes
- Minor cleanups in the C++ binding reduce stdout noise; we do not call explicit `deinitialize()` on tetgenio — resources are freed when objects go out of scope.
- If you want VTU output, install `meshio` (`pip install meshio`) and use the demo’s export code.


## TetGen Build Instructions

This directory provides two build targets:

1. **TetGen CLI** – the standalone command-line tool  
2. **TetGen Python Binding** – a shared library (`.so`) that exposes TetGen through `pybind11`

---

### 1. Build TetGen CLI

```bash
cd tetgen
mkdir build && cd build
cmake ..
make -j
```

This produces the `tetgen` executable inside `tetgen/build/`.

---

### 2. Build TetGen Python Binding (tetwrap)

```bash
cd tetwrap
mkdir build && cd build
cmake ..
make -j
```

This produces a dynamic library (e.g. _tetwrap.so) that can be imported from Python.

---

After building the Python binding, you can run the demo script:

```bash
python tetgen_volume_mesh_demo.py
```

## Documentation

Full TetGen manual: [TetGen 1.5 User's Manual (PDF)](https://wias-berlin.de/software/tetgen/1.5/doc/manual/manual.pdf)