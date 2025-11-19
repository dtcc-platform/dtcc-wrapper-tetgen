"""Unit tests for the switches module."""

import pytest

from dtcc_tetgen_wrapper import switches


class TestTetgenDefaults:
    """Test the tetgen_defaults function."""

    def test_returns_dict(self):
        """Test that tetgen_defaults returns a dictionary."""
        result = switches.tetgen_defaults()
        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        """Test that default config has all expected keys."""
        result = switches.tetgen_defaults()
        expected_keys = {
            "plc", "facet_constraints", "quality", "max_volume",
            "max_steiner_points", "coarsen", "weighted_delaunay",
            "no_merge", "detect_intersection", "check_consistency",
            "quiet", "verbose", "reconstruct", "insertaddpoints",
            "regionattrib", "convex", "conforming", "assign_region_attrib",
            "edge_output", "face_output", "neighbor_output",
            "tet_output_mode", "order", "output_mesh_dim"
        }
        assert set(result.keys()) == expected_keys

    def test_default_values(self):
        """Test that default values are correct."""
        result = switches.tetgen_defaults()
        assert result["plc"] is True
        assert result["quality"] is True
        assert result["quiet"] is None
        assert result["verbose"] is False
        assert result["order"] == 1


class TestFmtNum:
    """Test the _fmt_num helper function."""

    def test_format_boolean_true(self):
        """Test formatting of True boolean."""
        assert switches._fmt_num(True) == ""

    def test_format_boolean_false(self):
        """Test formatting of False boolean."""
        assert switches._fmt_num(False) == "0"

    def test_format_integer(self):
        """Test formatting of integers."""
        assert switches._fmt_num(42) == "42"
        assert switches._fmt_num(0) == "0"
        assert switches._fmt_num(-5) == "-5"

    def test_format_float(self):
        """Test formatting of floats."""
        assert switches._fmt_num(1.5) == "1.5"
        assert switches._fmt_num(0.1) == "0.1"
        assert switches._fmt_num(1.0) == "1"  # Drops decimal for whole numbers


class TestEmitQ:
    """Test the _emit_q helper function."""

    def test_quality_true(self):
        """Test quality flag when True."""
        result = switches._emit_q({"quality": True})
        assert result == "q"

    def test_quality_with_ratio(self):
        """Test quality flag with max_radius_edge_ratio."""
        result = switches._emit_q({"quality": True, "max_radius_edge_ratio": 2.0})
        assert result == "q2"

    def test_quality_with_angle(self):
        """Test quality flag with min_dihedral_angle."""
        result = switches._emit_q({"quality": True, "min_dihedral_angle": 15})
        assert result == "q15"

    def test_quality_with_both_parameters(self):
        """Test quality flag with both ratio and angle."""
        result = switches._emit_q({
            "quality": True,
            "max_radius_edge_ratio": 2.0,
            "min_dihedral_angle": 15
        })
        assert result == "q2/15"

    def test_quality_false(self):
        """Test no quality flag when False."""
        result = switches._emit_q({"quality": False})
        assert result == ""


class TestBuildTetgenSwitches:
    """Test the build_tetgen_switches function."""

    def test_default_switches(self):
        """Test building switches with default configuration."""
        result = switches.build_tetgen_switches()
        assert "p" in result  # plc flag
        assert "q" in result  # quality flag

    def test_override_defaults(self):
        """Test overriding default values."""
        result = switches.build_tetgen_switches(verbose=True, quiet=True)
        assert "V" in result  # verbose flag
        assert "Q" in result  # quiet flag

    def test_disable_defaults(self):
        """Test disabling default flags."""
        result = switches.build_tetgen_switches(plc=False, quality=False)
        assert "p" not in result
        assert "q" not in result

    def test_max_volume(self):
        """Test max_volume parameter."""
        result = switches.build_tetgen_switches(max_volume=0.1)
        assert "a0.1" in result

    def test_max_steiner_points(self):
        """Test max_steiner_points parameter."""
        result = switches.build_tetgen_switches(max_steiner_points=1000)
        assert "S1000" in result

    def test_coarsen(self):
        """Test coarsen parameter."""
        result = switches.build_tetgen_switches(coarsen=100)
        assert "R" in result

    def test_weighted_delaunay(self):
        """Test weighted_delaunay parameter."""
        result = switches.build_tetgen_switches(weighted_delaunay=True)
        assert "w" in result

    def test_no_merge(self):
        """Test no_merge parameter."""
        result = switches.build_tetgen_switches(no_merge=True)
        assert "M" in result

    def test_detect_intersection(self):
        """Test detect_intersection parameter."""
        result = switches.build_tetgen_switches(detect_intersection=True)
        assert "d" in result

    def test_check_consistency(self):
        """Test check_consistency parameter."""
        result = switches.build_tetgen_switches(check_consistency=True)
        assert "C" in result

    def test_reconstruct(self):
        """Test reconstruct parameter."""
        result = switches.build_tetgen_switches(reconstruct=True)
        assert "r" in result

    def test_insertaddpoints(self):
        """Test insertaddpoints parameter."""
        result = switches.build_tetgen_switches(insertaddpoints=True)
        assert "i" in result

    def test_regionattrib(self):
        """Test regionattrib parameter."""
        result = switches.build_tetgen_switches(regionattrib=True)
        assert "A" in result

    def test_convex(self):
        """Test convex parameter."""
        result = switches.build_tetgen_switches(convex=True)
        assert "c" in result

    def test_conforming(self):
        """Test conforming parameter."""
        result = switches.build_tetgen_switches(conforming=True)
        assert "D" in result

    def test_assign_region_attrib(self):
        """Test assign_region_attrib parameter."""
        result = switches.build_tetgen_switches(assign_region_attrib=True)
        assert "AA" in result

    def test_output_flags(self):
        """Test various output flags."""
        result = switches.build_tetgen_switches(
            edge_output=True,
            face_output=True,
            neighbor_output=True
        )
        assert "e" in result  # edges
        assert "f" in result  # faces
        assert "n" in result  # neighbors

    def test_order_parameter(self):
        """Test order parameter for second-order tets."""
        result = switches.build_tetgen_switches(order=2)
        assert "o2" in result

    def test_output_mesh_dim(self):
        """Test output_mesh_dim parameter."""
        result = switches.build_tetgen_switches(output_mesh_dim=2)
        assert "g" in result

    def test_tet_output_mode(self):
        """Test tet_output_mode parameter."""
        # Mode 0 (default) - no flag
        result = switches.build_tetgen_switches(tet_output_mode=0)
        assert "z" not in result

        # Mode 1 - compress with zero
        result = switches.build_tetgen_switches(tet_output_mode=1)
        assert "z" in result

    def test_complex_switches(self):
        """Test building complex combination of switches."""
        result = switches.build_tetgen_switches(
            quality=True,
            max_radius_edge_ratio=2.0,
            min_dihedral_angle=15,
            max_volume=0.01,
            verbose=True,
            edge_output=True,
            face_output=True
        )
        assert "pq2/15" in result
        assert "a0.01" in result
        assert "V" in result
        assert "e" in result
        assert "f" in result

    def test_params_dict(self):
        """Test passing parameters as dict."""
        params = {
            "quality": False,
            "verbose": True,
            "max_volume": 0.5
        }
        result = switches.build_tetgen_switches(params)
        assert "q" not in result  # quality disabled
        assert "V" in result       # verbose enabled
        assert "a0.5" in result    # max_volume set

    def test_params_dict_with_overrides(self):
        """Test params dict with keyword overrides."""
        params = {
            "quality": False,
            "verbose": False
        }
        result = switches.build_tetgen_switches(params, verbose=True)
        assert "V" in result  # override wins