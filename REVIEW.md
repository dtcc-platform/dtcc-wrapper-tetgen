# Code Review

## Summary
- `tetwrap.__all__` exports a non-existent `build_volume_mesh_ex` symbol. Importers will hit `AttributeError`. Recommend removing or defining the symbol.

## Details
1. `tetwrap/__init__.py` includes `"build_volume_mesh_ex"` in `__all__`, but the module never defines it. Any `from tetwrap import build_volume_mesh_ex` will raise. Either implement the function or drop it from `__all__`.

