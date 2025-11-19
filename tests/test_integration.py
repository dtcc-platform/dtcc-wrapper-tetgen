"""Integration tests for dtcc-wrapper-tetgen."""

import numpy as np
import pytest

from dtcc_tetgen_wrapper import build_tetgen_switches, tetrahedralize


@pytest.mark.integration
class TestIntegration:
    """End-to-end integration tests."""

    def test_full_pipeline_cube(self):
        """Test complete pipeline with a cube mesh."""
        # Create cube vertices
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=np.float64)

        # Define boundary facets with labels
        boundary_facets = {
            "bottom": [[0, 3, 2, 1]],
            "top": [[4, 5, 6, 7]],
            "front": [[0, 1, 5, 4]],
            "back": [[2, 3, 7, 6]],
            "left": [[0, 4, 7, 3]],
            "right": [[1, 2, 6, 5]],
        }

        # Build custom switches
        switches = build_tetgen_switches(
            quality=True,
            max_volume=0.1,
            face_output=True,
            neighbor_output=True,
            quiet=True
        )

        # Run tetrahedralization
        result = tetrahedralize(
            vertices,
            boundary_facets=boundary_facets,
            tetgen_switches=switches,
            return_io=True
        )

        # Validate result
        assert result.points.shape[0] >= 8  # At least original vertices
        assert result.points.shape[1] == 3  # 3D points
        assert result.tets.shape[0] >= 5    # At least 5 tets for cube
        assert result.tri_faces is not None
        assert result.neighbors is not None
        assert result.face_markers is not None
        assert len(result.face_markers) == 6  # 6 boundary groups

        # Check that boundary faces are properly indexed
        for label, indices in result.face_markers.items():
            assert label in boundary_facets
            assert all(0 <= idx < result.tri_faces.shape[0] for idx in indices)

    def test_pipeline_with_interior_point(self):
        """Test with an interior point that should be included."""
        # Cube vertices plus center point
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
            [0.5, 0.5, 0.5],  # Center point
        ], dtype=np.float64)

        # Cube faces (not including center point)
        faces = np.array([
            [0, 3, 2, 1],  # bottom
            [4, 5, 6, 7],  # top
            [0, 1, 5, 4],  # front
            [2, 3, 7, 6],  # back
            [0, 4, 7, 3],  # left
            [1, 2, 6, 5],  # right
        ], dtype=np.int32)

        result = tetrahedralize(vertices, faces=faces, return_io=True)

        # Should include all 9 vertices
        assert result.points.shape[0] >= 9
        # Center point should create more tetrahedra
        assert result.tets.shape[0] > 5

    def test_pipeline_quality_refinement(self):
        """Test quality refinement with different parameters."""
        vertices = np.array([
            [0, 0, 0], [2, 0, 0], [2, 1, 0], [0, 1, 0],
            [0, 0, 1], [2, 0, 1], [2, 1, 1], [0, 1, 1],
        ], dtype=np.float64)

        # Coarse mesh
        coarse = tetrahedralize(
            vertices,
            quality=False,
            return_io=True
        )

        # Medium quality
        medium = tetrahedralize(
            vertices,
            quality=True,
            max_radius_edge_ratio=2.0,
            return_io=True
        )

        # High quality
        fine = tetrahedralize(
            vertices,
            quality=True,
            max_radius_edge_ratio=1.2,
            min_dihedral_angle=20,
            return_io=True
        )

        # Higher quality should produce more elements
        assert fine.tets.shape[0] >= medium.tets.shape[0]
        assert medium.tets.shape[0] >= coarse.tets.shape[0]

    def test_pipeline_with_regions(self):
        """Test with region attributes."""
        # Two stacked cubes
        vertices = np.array([
            # Lower cube
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
            # Upper cube (sharing top face of lower)
            [0, 0, 2], [1, 0, 2], [1, 1, 2], [0, 1, 2],
        ], dtype=np.float64)

        # Faces for both cubes
        faces = np.array([
            # Lower cube
            [0, 3, 2, 1],  # bottom
            [4, 5, 6, 7],  # middle (shared)
            [0, 1, 5, 4],  # front-lower
            [2, 3, 7, 6],  # back-lower
            [0, 4, 7, 3],  # left-lower
            [1, 2, 6, 5],  # right-lower
            # Upper cube
            [8, 9, 10, 11],  # top
            [4, 5, 9, 8],    # front-upper
            [6, 7, 11, 10],  # back-upper
            [4, 8, 11, 7],   # left-upper
            [5, 6, 10, 9],   # right-upper
        ], dtype=np.int32)

        result = tetrahedralize(
            vertices,
            faces=faces,
            regionattrib=True,
            return_io=True
        )

        assert result.points.shape[0] >= 12
        assert result.tets.shape[0] >= 10  # At least 5 tets per cube

    def test_error_recovery(self):
        """Test error handling and recovery."""
        # Invalid: too few vertices
        with pytest.raises(ValueError, match="at least 4"):
            tetrahedralize(np.array([[0, 0, 0], [1, 0, 0]]))

        # Invalid: wrong shape
        with pytest.raises(ValueError, match="shape.*3"):
            tetrahedralize(np.array([[0, 0], [1, 1], [2, 2], [3, 3]]))

        # Invalid: out of bounds faces
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float64)
        faces = np.array([[0, 1, 100]])  # vertex 100 doesn't exist
        with pytest.raises(ValueError, match="out of range"):
            tetrahedralize(vertices, faces=faces)

    def test_deterministic_output(self):
        """Test that output is deterministic for same input."""
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
        ], dtype=np.float64)

        # Run twice with same parameters
        result1 = tetrahedralize(vertices, quality=False, quiet=True, return_io=True)
        result2 = tetrahedralize(vertices, quality=False, quiet=True, return_io=True)

        # Should produce same number of elements
        assert result1.points.shape == result2.points.shape
        assert result1.tets.shape == result2.tets.shape

    @pytest.mark.slow
    def test_stress_random_points(self):
        """Stress test with random point clouds."""
        np.random.seed(42)

        for n_points in [10, 50, 100, 500]:
            # Generate random points in unit cube
            vertices = np.random.rand(n_points, 3)

            try:
                result = tetrahedralize(
                    vertices,
                    quality=True,
                    quiet=True,
                    return_io=True
                )

                # Basic validation
                assert result.points.shape[0] >= n_points
                assert result.tets.shape[0] > 0
                assert result.tets.shape[1] == result.corners

            except Exception as e:
                pytest.fail(f"Failed with {n_points} random points: {e}")