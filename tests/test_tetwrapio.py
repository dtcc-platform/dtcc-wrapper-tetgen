"""Unit tests for the tetwrapio module."""

import numpy as np
import pytest
from dtcc_wrapper_tetgen.tetwrapio import TetwrapIO


class TestTetwrapIO:
    """Test the TetwrapIO dataclass."""

    def test_create_minimal(self):
        """Test creating TetwrapIO with minimal data."""
        points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        tets = np.array([[0, 1, 2, 0]], dtype=np.int32)

        io = TetwrapIO(points=points, tets=tets, corners=4)

        assert io.points is points
        assert io.tets is tets
        assert io.corners == 4
        assert io.switches == ""

    def test_create_with_all_fields(self):
        """Test creating TetwrapIO with all fields."""
        points = np.array([[0, 0, 0], [1, 0, 0]], dtype=np.float64)
        tets = np.array([[0, 1, 0, 0]], dtype=np.int32)
        tri_faces = np.array([[0, 1, 0]], dtype=np.int32)
        tri_markers = np.array([1], dtype=np.int32)
        edges = np.array([[0, 1]], dtype=np.int32)
        edge_markers = np.array([2], dtype=np.int32)
        neighbors = np.array([[0, 1, 2, 3]], dtype=np.int32)
        face_markers = {"boundary": [0]}

        io = TetwrapIO(
            points=points,
            tets=tets,
            corners=4,
            switches="pq",
            tri_faces=tri_faces,
            tri_markers=tri_markers,
            edges=edges,
            edge_markers=edge_markers,
            neighbors=neighbors,
            face_markers=face_markers
        )

        assert io.points is points
        assert io.tets is tets
        assert io.corners == 4
        assert io.switches == "pq"
        assert io.tri_faces is tri_faces
        assert io.tri_markers is tri_markers
        assert io.edges is edges
        assert io.edge_markers is edge_markers
        assert io.neighbors is neighbors
        assert io.face_markers == face_markers

    def test_normalize_markers_none(self):
        """Test _normalize_marker_array with None input."""
        io = TetwrapIO(
            points=np.array([[0, 0, 0]], dtype=np.float64),
            tets=np.array([[0, 0, 0, 0]], dtype=np.int32),
            corners=4
        )
        io._normalize_marker_array(None)
        # Should not raise any error

    def test_normalize_markers_empty(self):
        """Test _normalize_marker_array with empty array."""
        io = TetwrapIO(
            points=np.array([[0, 0, 0]], dtype=np.float64),
            tets=np.array([[0, 0, 0, 0]], dtype=np.int32),
            corners=4
        )
        markers = np.array([], dtype=np.int32)
        io._normalize_marker_array(markers)
        # Should not modify empty array
        assert len(markers) == 0

    def test_normalize_markers_positive(self):
        """Test _normalize_marker_array with positive markers."""
        io = TetwrapIO(
            points=np.array([[0, 0, 0]], dtype=np.float64),
            tets=np.array([[0, 0, 0, 0]], dtype=np.int32),
            corners=4
        )
        markers = np.array([1, 2, 3], dtype=np.int32)
        original = markers.copy()
        io._normalize_marker_array(markers)
        # Positive markers should be decremented by 1
        np.testing.assert_array_equal(markers, original - 1)

    def test_normalize_markers_zeros(self):
        """Test _normalize_marker_array with zero markers."""
        io = TetwrapIO(
            points=np.array([[0, 0, 0]], dtype=np.float64),
            tets=np.array([[0, 0, 0, 0]], dtype=np.int32),
            corners=4
        )
        markers = np.array([0, 0, 0], dtype=np.int32)
        io._normalize_marker_array(markers)
        # Zero markers should become -1
        np.testing.assert_array_equal(markers, [-1, -1, -1])

    def test_normalize_markers_mixed(self):
        """Test _normalize_marker_array with mixed markers."""
        io = TetwrapIO(
            points=np.array([[0, 0, 0]], dtype=np.float64),
            tets=np.array([[0, 0, 0, 0]], dtype=np.int32),
            corners=4
        )
        markers = np.array([0, 1, 2, 0, 3], dtype=np.int32)
        io._normalize_marker_array(markers)
        # 0 -> -1, positive -> decremented
        expected = np.array([-1, 0, 1, -1, 2], dtype=np.int32)
        np.testing.assert_array_equal(markers, expected)

    def test_normalize_on_creation(self):
        """Test that markers are normalized on creation."""
        points = np.array([[0, 0, 0], [1, 0, 0]], dtype=np.float64)
        tets = np.array([[0, 1, 0, 0]], dtype=np.int32)
        tri_markers = np.array([1, 2, 0], dtype=np.int32)
        edge_markers = np.array([0, 3, 4], dtype=np.int32)

        io = TetwrapIO(
            points=points,
            tets=tets,
            corners=4,
            tri_markers=tri_markers,
            edge_markers=edge_markers
        )

        # Check that markers were normalized
        np.testing.assert_array_equal(io.tri_markers, [0, 1, -1])
        np.testing.assert_array_equal(io.edge_markers, [-1, 2, 3])

    def test_boundary_tri_faces_property(self):
        """Test boundary_tri_faces property."""
        points = np.array([[0, 0, 0]], dtype=np.float64)
        tets = np.array([[0, 0, 0, 0]], dtype=np.int32)

        # Without face_markers
        io = TetwrapIO(points=points, tets=tets, corners=4)
        assert io.boundary_tri_faces is None

        # With face_markers
        face_markers = {"boundary": [0, 1, 2]}
        io = TetwrapIO(points=points, tets=tets, corners=4, face_markers=face_markers)
        assert io.boundary_tri_faces == [0, 1, 2]

    def test_boundary_tri_markers_property(self):
        """Test boundary_tri_markers property."""
        points = np.array([[0, 0, 0]], dtype=np.float64)
        tets = np.array([[0, 0, 0, 0]], dtype=np.int32)
        tri_markers = np.array([1, 2, 3], dtype=np.int32)

        # Without face_markers
        io = TetwrapIO(
            points=points,
            tets=tets,
            corners=4,
            tri_markers=tri_markers
        )
        assert io.boundary_tri_markers is None

        # With face_markers
        face_markers = {"boundary": [0, 2]}  # Select indices 0 and 2
        io = TetwrapIO(
            points=points,
            tets=tets,
            corners=4,
            tri_markers=tri_markers,
            face_markers=face_markers
        )
        # Should return markers at indices 0 and 2 (after normalization)
        expected = np.array([0, 2], dtype=np.int32)  # After normalization
        np.testing.assert_array_equal(io.boundary_tri_markers, expected)