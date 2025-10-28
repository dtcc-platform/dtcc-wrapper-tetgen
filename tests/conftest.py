"""Pytest configuration and fixtures for dtcc-wrapper-tetgen tests."""

import numpy as np
import pytest


@pytest.fixture
def unit_cube_vertices():
    """Create vertices for a unit cube."""
    return np.array([
        [0.0, 0.0, 0.0],  # 0
        [1.0, 0.0, 0.0],  # 1
        [1.0, 1.0, 0.0],  # 2
        [0.0, 1.0, 0.0],  # 3
        [0.0, 0.0, 1.0],  # 4
        [1.0, 0.0, 1.0],  # 5
        [1.0, 1.0, 1.0],  # 6
        [0.0, 1.0, 1.0],  # 7
    ], dtype=np.float64)


@pytest.fixture
def unit_cube_faces():
    """Create face indices for a unit cube (counter-clockwise from outside)."""
    return np.array([
        [0, 3, 2, 1],  # bottom (z=0)
        [4, 5, 6, 7],  # top (z=1)
        [0, 1, 5, 4],  # front (y=0)
        [2, 3, 7, 6],  # back (y=1)
        [0, 4, 7, 3],  # left (x=0)
        [1, 2, 6, 5],  # right (x=1)
    ], dtype=np.int32)


@pytest.fixture
def unit_cube_boundary_facets():
    """Create boundary facets dictionary for unit cube."""
    return {
        "bottom": [[0, 3, 2, 1]],
        "top": [[4, 5, 6, 7]],
        "front": [[0, 1, 5, 4]],
        "back": [[2, 3, 7, 6]],
        "left": [[0, 4, 7, 3]],
        "right": [[1, 2, 6, 5]],
    }


@pytest.fixture
def simple_tetrahedron_vertices():
    """Create vertices for a simple tetrahedron."""
    return np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float64)


@pytest.fixture
def simple_tetrahedron_faces():
    """Create face indices for a simple tetrahedron."""
    return np.array([
        [0, 2, 1],  # bottom
        [0, 1, 3],  # front
        [0, 3, 2],  # left
        [1, 2, 3],  # diagonal
    ], dtype=np.int32)


@pytest.fixture
def invalid_vertices():
    """Create various invalid vertex inputs for testing error handling."""
    return {
        "wrong_shape_2d": np.array([[0, 0], [1, 1]]),
        "wrong_shape_4d": np.array([[0, 0, 0, 0], [1, 1, 1, 1]]),
        "wrong_type": [[0, 0, 0], [1, 1, 1]],  # list instead of array
        "empty": np.array([]),
        "single_point": np.array([[0, 0, 0]]),
        "two_points": np.array([[0, 0, 0], [1, 1, 1]]),
    }


@pytest.fixture
def invalid_faces():
    """Create various invalid face inputs for testing error handling."""
    return {
        "wrong_shape": np.array([[0, 1], [1, 2]]),  # 2 vertices per face
        "out_of_bounds": np.array([[0, 1, 100]]),  # vertex index 100 doesn't exist
        "negative_index": np.array([[0, 1, -1]]),  # negative vertex index
        "wrong_type": [[0, 1, 2]],  # list instead of array
        "empty": np.array([]),
    }