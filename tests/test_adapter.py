"""Unit tests for the adapter module."""

import numpy as np
import pytest
from dtcc_tetgen_wrapper import tetrahedralize
from dtcc_tetgen_wrapper.tetwrapio import TetwrapIO


class TestTetrahedralizeValidation:
    """Test input validation for tetrahedralize function."""

    def test_vertices_validation_wrong_shape(self, invalid_vertices):
        """Test that wrong shaped vertices raise ValueError."""
        # 2D vertices
        with pytest.raises(ValueError, match="must be shape.*3"):
            tetrahedralize(invalid_vertices["wrong_shape_2d"])

        # 4D vertices
        with pytest.raises(ValueError, match="must be shape.*3"):
            tetrahedralize(invalid_vertices["wrong_shape_4d"])

    def test_vertices_validation_too_few_points(self, invalid_vertices):
        """Test that too few vertices raise ValueError."""
        # Empty vertices
        with pytest.raises(ValueError, match="at least 4"):
            tetrahedralize(invalid_vertices["empty"])

        # Single point
        with pytest.raises(ValueError, match="at least 4"):
            tetrahedralize(invalid_vertices["single_point"])

        # Two points
        with pytest.raises(ValueError, match="at least 4"):
            tetrahedralize(invalid_vertices["two_points"])

    def test_vertices_validation_wrong_dtype(self):
        """Test that integer vertices are converted properly."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.int32)
        # Should not raise - adapter should handle conversion
        io = tetrahedralize(vertices, return_io=True)
        assert io.points.dtype == np.float64

    def test_faces_validation_wrong_shape(self, simple_tetrahedron_vertices):
        """Test that wrong shaped faces raise ValueError."""
        faces = np.array([[0, 1], [1, 2]])  # 2 vertices per face
        with pytest.raises(ValueError, match="must be shape.*3"):
            tetrahedralize(simple_tetrahedron_vertices, faces=faces)

    def test_faces_validation_out_of_bounds(self, simple_tetrahedron_vertices):
        """Test that out-of-bounds face indices raise ValueError."""
        faces = np.array([[0, 1, 100]])  # vertex 100 doesn't exist
        with pytest.raises(ValueError, match="out of range"):
            tetrahedralize(simple_tetrahedron_vertices, faces=faces)

    def test_faces_validation_negative_index(self, simple_tetrahedron_vertices):
        """Test that negative face indices raise ValueError."""
        faces = np.array([[0, 1, -1]])
        with pytest.raises(ValueError, match="Face indices must be non-negative"):
            tetrahedralize(simple_tetrahedron_vertices, faces=faces)

    def test_boundary_facets_validation(self, unit_cube_vertices):
        """Test boundary facets validation."""
        # Non-dictionary input
        with pytest.raises(ValueError, match="must be a dictionary"):
            tetrahedralize(unit_cube_vertices, boundary_facets=[])

        # Non-list values
        boundary_facets = {"top": [[0, 1, 2]], "bottom": "not_a_list"}
        with pytest.raises(ValueError, match="must be a list"):
            tetrahedralize(unit_cube_vertices, boundary_facets=boundary_facets)


class TestTetrahedralizeSimple:
    """Test tetrahedralize with simple geometries."""

    def test_tetrahedron(self, simple_tetrahedron_vertices):
        """Test meshing a simple tetrahedron."""
        result = tetrahedralize(simple_tetrahedron_vertices, return_io=True)

        assert isinstance(result, TetwrapIO)
        assert result.points.shape[0] >= 4  # At least original vertices
        assert result.points.shape[1] == 3  # 3D points
        assert result.tets.shape[0] >= 1    # At least one tetrahedron
        assert result.tets.shape[1] == result.corners  # Correct corners

    def test_tetrahedron_with_faces(self, simple_tetrahedron_vertices, simple_tetrahedron_faces):
        """Test meshing a tetrahedron with face constraints."""
        result = tetrahedralize(
            simple_tetrahedron_vertices,
            faces=simple_tetrahedron_faces,
            return_io=True
        )

        assert isinstance(result, TetwrapIO)
        assert result.points.shape[0] >= 4
        assert result.tets.shape[0] >= 1

    def test_cube(self, unit_cube_vertices, unit_cube_faces):
        """Test meshing a unit cube."""
        result = tetrahedralize(
            unit_cube_vertices,
            faces=unit_cube_faces,
            return_io=True
        )

        assert isinstance(result, TetwrapIO)
        assert result.points.shape[0] >= 8  # At least original vertices
        assert result.tets.shape[0] >= 5    # Cube needs at least 5 tets

    def test_cube_with_boundary_facets(self, unit_cube_vertices, unit_cube_boundary_facets):
        """Test meshing a cube with boundary facets."""
        result = tetrahedralize(
            unit_cube_vertices,
            boundary_facets=unit_cube_boundary_facets,
            return_io=True
        )

        assert isinstance(result, TetwrapIO)
        assert result.face_markers is not None
        # Should have 6 boundary groups
        assert len(result.face_markers) == 6


class TestTetrahedralizeReturnOptions:
    """Test different return options for tetrahedralize."""

    def test_return_io(self, simple_tetrahedron_vertices):
        """Test returning TetwrapIO object."""
        result = tetrahedralize(simple_tetrahedron_vertices, return_io=True)
        assert isinstance(result, TetwrapIO)

    def test_return_default(self, simple_tetrahedron_vertices):
        """Test default return (points and tets)."""
        result = tetrahedralize(simple_tetrahedron_vertices)
        assert isinstance(result, tuple)
        assert len(result) == 2
        points, tets = result
        assert isinstance(points, np.ndarray)
        assert isinstance(tets, np.ndarray)

    def test_return_with_faces(self, unit_cube_vertices, unit_cube_faces):
        """Test returning with face output."""
        result = tetrahedralize(
            unit_cube_vertices,
            faces=unit_cube_faces,
            return_faces=True
        )
        assert isinstance(result, tuple)
        assert len(result) == 3
        points, tets, tri_faces = result
        assert tri_faces is not None
        assert isinstance(tri_faces, np.ndarray)

    def test_return_with_edges(self, simple_tetrahedron_vertices):
        """Test returning with edge output."""
        result = tetrahedralize(
            simple_tetrahedron_vertices,
            return_edges=True
        )
        assert isinstance(result, tuple)
        assert len(result) == 4  # points, tets, faces, edges
        points, tets, tri_faces, edges = result
        assert edges is not None
        assert isinstance(edges, np.ndarray)

    def test_return_with_neighbors(self, simple_tetrahedron_vertices):
        """Test returning with neighbor output."""
        result = tetrahedralize(
            simple_tetrahedron_vertices,
            return_neighbors=True
        )
        assert isinstance(result, tuple)
        assert len(result) == 5  # points, tets, faces, edges, neighbors
        points, tets, tri_faces, edges, neighbors = result
        assert neighbors is not None
        assert isinstance(neighbors, np.ndarray)

    def test_return_with_boundary(self, unit_cube_vertices, unit_cube_boundary_facets):
        """Test returning with boundary information."""
        result = tetrahedralize(
            unit_cube_vertices,
            boundary_facets=unit_cube_boundary_facets,
            return_boundary=True
        )
        assert isinstance(result, tuple)
        assert len(result) == 7
        points, tets, tri_faces, edges, neighbors, boundary_faces, boundary_markers = result
        assert boundary_faces is not None
        assert boundary_markers is not None


class TestTetrahedralizeSwitches:
    """Test tetrahedralize with various switch configurations."""

    def test_quality_control(self, unit_cube_vertices, unit_cube_faces):
        """Test quality control parameters."""
        # Default quality
        result1 = tetrahedralize(
            unit_cube_vertices,
            faces=unit_cube_faces,
            return_io=True
        )

        # Stricter quality
        result2 = tetrahedralize(
            unit_cube_vertices,
            faces=unit_cube_faces,
            max_radius_edge_ratio=1.5,
            min_dihedral_angle=20,
            return_io=True
        )

        # Stricter quality often produces more tetrahedra
        assert result2.tets.shape[0] >= result1.tets.shape[0]

    def test_max_volume(self, unit_cube_vertices, unit_cube_faces):
        """Test max volume constraint."""
        # Large max volume
        result1 = tetrahedralize(
            unit_cube_vertices,
            faces=unit_cube_faces,
            max_volume=1.0,
            return_io=True
        )

        # Small max volume should create more tets
        result2 = tetrahedralize(
            unit_cube_vertices,
            faces=unit_cube_faces,
            max_volume=0.01,
            return_io=True
        )

        assert result2.tets.shape[0] > result1.tets.shape[0]

    def test_quiet_verbose(self, simple_tetrahedron_vertices):
        """Test quiet and verbose flags."""
        # Should not raise errors
        tetrahedralize(simple_tetrahedron_vertices, quiet=True)
        tetrahedralize(simple_tetrahedron_vertices, verbose=True)

    def test_custom_switches(self, simple_tetrahedron_vertices):
        """Test with custom tetgen_switches string."""
        result = tetrahedralize(
            simple_tetrahedron_vertices,
            tetgen_switches="pqQ",  # plc, quality, quiet
            return_io=True
        )
        assert result.switches == "pqQ"


class TestTetrahedralizeEdgeCases:
    """Test edge cases and error conditions."""

    def test_coplanar_points(self):
        """Test handling of coplanar points."""
        # All points in z=0 plane
        vertices = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
        ], dtype=np.float64)

        # Should handle gracefully, possibly with warning
        # TetGen might add points or fail depending on switches
        with pytest.raises(Exception):
            # This should fail as points are coplanar
            tetrahedralize(vertices, plc=False)

    def test_duplicate_vertices(self):
        """Test handling of duplicate vertices."""
        vertices = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0, 0, 0],  # Duplicate of first vertex
        ], dtype=np.float64)

        # Should handle duplicates
        result = tetrahedralize(vertices, return_io=True)
        # TetGen typically removes duplicates
        assert result.points.shape[0] <= 5

    def test_large_mesh(self):
        """Test with a larger mesh."""
        # Create a grid of points
        x = np.linspace(0, 1, 5)
        y = np.linspace(0, 1, 5)
        z = np.linspace(0, 1, 5)
        xx, yy, zz = np.meshgrid(x, y, z)
        vertices = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])

        result = tetrahedralize(vertices, return_io=True)
        assert result.points.shape[0] >= 125  # Original vertices
        assert result.tets.shape[0] > 0

    @pytest.mark.slow
    def test_performance_large_mesh(self):
        """Test performance with very large mesh."""
        # Create a larger grid
        x = np.linspace(0, 1, 10)
        y = np.linspace(0, 1, 10)
        z = np.linspace(0, 1, 10)
        xx, yy, zz = np.meshgrid(x, y, z)
        vertices = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])

        import time
        start = time.time()
        result = tetrahedralize(vertices, return_io=True)
        elapsed = time.time() - start

        assert result.points.shape[0] >= 1000
        assert result.tets.shape[0] > 0
        # Should complete in reasonable time (adjust as needed)
        assert elapsed < 10.0, f"Tetrahedralization took {elapsed:.2f}s"