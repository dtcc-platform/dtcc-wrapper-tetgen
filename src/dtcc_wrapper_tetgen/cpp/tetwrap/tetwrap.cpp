#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <vector>
#include <stdexcept>
#include <algorithm>
#include <array>
#include <map>

#include "tetgen.h"

namespace py = pybind11;

// ===================== Helper conversions =====================
static py::array_t<double> to_array_f64(const REAL* src, int n, int m)
{
    if (!src || n <= 0 || m <= 0) return py::array_t<double>();
    py::array_t<double> A({n, m});
    auto a = A.mutable_unchecked<2>();
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < m; ++j)
            a(i, j) = src[i * m + j];
    return A;
}

static py::array_t<int> to_array_i32(const int* src, int n, int m)
{
    if (!src || n <= 0 || m <= 0) return py::array_t<int>();
    py::array_t<int> A({n, m});
    auto a = A.mutable_unchecked<2>();
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < m; ++j)
            a(i, j) = src[i * m + j];
    return A;
}

static py::array_t<int> to_vector_i32(const int* src, int n)
{
    if (!src || n <= 0) return py::array_t<int>();
    py::array_t<int> A({n});
    auto a = A.mutable_unchecked<1>();
    for (int i = 0; i < n; ++i)
        a(i) = src[i];
    return A;
}

static py::array_t<double> to_vector_f64(const REAL* src, int n)
{
    if (!src || n <= 0) return py::array_t<double>();
    py::array_t<double> A({n});
    auto a = A.mutable_unchecked<1>();
    for (int i = 0; i < n; ++i)
        a(i) = src[i];
    return A;
}

// ===================== Rich IO result =====================
struct TetwrapIO {
    py::array points;         // (N,3) float64
    py::array tets;           // (K,4/10) int32
    py::object tri_faces;     // (F,3) int32 or None
    py::object tri_markers;   // (F,) int32 or None
    py::object boundary_tri_faces; // (BF,3) int32 or None
    py::object boundary_tri_markers; // (BF,) int32 or None
    py::object edges;         // (E,2) int32 or None
    py::object edge_markers;  // (E,) int32 or None
    py::object neighbors;     // (K,4) int32 or None
    py::object point_markers; // (N,) int32 or None
    py::object tet_attr;      // (K,A) float64 or None
    py::object tet_vol;       // (K,) float64 or None
    int corners = 4;
    std::string switches;
};

// Convert TetGen output to NumPy (vertices, tets)
static std::pair<py::array_t<double>, py::array_t<int>>
to_numpy(const tetgenio &out)
{
    const int N = out.numberofpoints;
    const int K = out.numberoftetrahedra;
    const int corners = out.numberofcorners; // typically 4, but could be 10 for higher order

    py::array_t<double> V({N, 3});
    {
        auto v = V.mutable_unchecked<2>();
        for (int i = 0; i < N; ++i)
        {
            v(i, 0) = out.pointlist[3 * i + 0];
            v(i, 1) = out.pointlist[3 * i + 1];
            v(i, 2) = out.pointlist[3 * i + 2];
        }
    }

    py::array_t<int> T({K, corners});
    {
        auto t = T.mutable_unchecked<2>();
        for (int i = 0; i < K; ++i)
        {
            for (int j = 0; j < corners; ++j)
            {
                t(i, j) = out.tetrahedronlist[i * corners + j];
            }
        }
    }

    return {V, T};
}

// (T,4) tets, (T,4) neighbors -> (B,3) boundary faces (indices into points)
static py::array_t<int> compute_boundary_face_tris(
    const py::array_t<int, py::array::c_style | py::array::forcecast>& tets_,
    const py::array_t<int, py::array::c_style | py::array::forcecast>& nbrs_)
{
    if (tets_.ndim() != 2 || tets_.shape(1) != 4)
        throw std::runtime_error("tets must have shape (T,4)");
    if (nbrs_.ndim() != 2 || nbrs_.shape(1) != 4)
        throw std::runtime_error("neighbors must have shape (T,4)");
    if (tets_.shape(0) != nbrs_.shape(0))
        throw std::runtime_error("tets and neighbors must have same length");

    auto tets = tets_.unchecked<2>();
    auto nbrs = nbrs_.unchecked<2>();
    const ssize_t T = tets.shape(0);

    // local face patterns: face opposite vertex k
    const int faces_of_tet[4][3] = {
        {1,2,3},  // opposite 0
        {0,3,2},  // opposite 1
        {0,1,3},  // opposite 2
        {0,2,1}   // opposite 3
    };

    // First pass: count boundary faces
    ssize_t B = 0;
    for (ssize_t i = 0; i < T; ++i)
        for (int lf = 0; lf < 4; ++lf)
            if (nbrs(i, lf) < 0) ++B;

    // Allocate (B,3) int32
    py::array_t<int> faces({B, (ssize_t)3});
    auto F = faces.mutable_unchecked<2>();

    // Second pass: fill
    ssize_t b = 0;
    for (ssize_t i = 0; i < T; ++i) {
        for (int lf = 0; lf < 4; ++lf) {
            if (nbrs(i, lf) < 0) {
                const int* pat = faces_of_tet[lf];
                F(b,0) = tets(i, pat[0]);
                F(b,1) = tets(i, pat[1]);
                F(b,2) = tets(i, pat[2]);
                ++b;
            }
        }
    }
    return faces;
}

// Core routine: run TetGen and produce rich IO
static TetwrapIO tetrahedralize_core(
    py::array_t<double, py::array::c_style | py::array::forcecast> vertices,
    py::array_t<int,    py::array::c_style | py::array::forcecast> mesh_facets,
    py::object mesh_facet_markers_obj,
    const std::vector<std::vector<int>> &boundary_facets,
    py::object tetgen_switches,
    bool compute_boundary_faces = true  )
{
    // Basic shape checks
    if (vertices.ndim() != 2 || vertices.shape(1) != 3)
        throw std::runtime_error("vertices must have shape (N,3)");
    if (mesh_facets.ndim() != 2 || mesh_facets.shape(1) != 3)
        throw std::runtime_error("mesh_facets must have shape (M,3)");
    if (boundary_facets.size() < 1)
        throw std::runtime_error("boundary_facets must contain at least one polygon (list of vertex indices)");

    auto V = vertices.unchecked<2>();
    auto F = mesh_facets.unchecked<2>();
    const int N = static_cast<int>(V.shape(0));
    const int M = static_cast<int>(F.shape(0));
    const int B = static_cast<int>(boundary_facets.size());
    py::array_t<int, py::array::c_style | py::array::forcecast> mesh_facet_markers;
    const int* mesh_facet_marker_ptr = nullptr;
    if (!mesh_facet_markers_obj.is_none()) {
        mesh_facet_markers = mesh_facet_markers_obj.cast<py::array_t<int, py::array::c_style | py::array::forcecast>>();
        if (mesh_facet_markers.ndim() != 1)
            throw std::runtime_error("mesh_facet_markers must be a 1D array");
        if (mesh_facet_markers.shape(0) != M)
            throw std::runtime_error("mesh_facet_markers length must match number of mesh facets");
        mesh_facet_marker_ptr = mesh_facet_markers.data();
    }

    if (N <= 0) throw std::runtime_error("vertices: N <= 0");
    if (M < 0)  throw std::runtime_error("mesh_facets: M < 0");

    // Index range checks
    for (int i = 0; i < M; ++i)
    {
        for (int k = 0; k < 3; ++k)
        {
            int vid = F(i, k);
            if (vid < 0 || vid >= N)
                throw std::runtime_error("mesh_facets index out of range at row " + std::to_string(i));
        }
    }
    for (size_t bi = 0; bi < boundary_facets.size(); ++bi)
    {
        const auto &poly = boundary_facets[bi];
        if (poly.size() < 3)
            throw std::runtime_error("boundary facet has fewer than 3 vertices: polygon " + std::to_string(bi));
        for (int vid : poly)
        {
            if (vid < 0 || vid >= N)
                throw std::runtime_error("boundary_facets index out of range at polygon " + std::to_string(bi));
        }
    }

    tetgenio in, out;

    // Points
    in.firstnumber = 0; // 0-based indexing
    in.numberofpoints = N;
    in.pointlist = new REAL[in.numberofpoints * 3];
    for (int i = 0; i < N; ++i)
    {
        in.pointlist[3 * i + 0] = static_cast<REAL>(V(i, 0));
        in.pointlist[3 * i + 1] = static_cast<REAL>(V(i, 1));
        in.pointlist[3 * i + 2] = static_cast<REAL>(V(i, 2));
    }

    // Facets: mesh triangles + boundary polygons
    const int T = M + B;
    in.numberoffacets = T;
    in.facetlist = new tetgenio::facet[in.numberoffacets]();
    // Provide facet markers so output tri faces carry labels on boundary
    in.facetmarkerlist = new int[in.numberoffacets];

    // Mesh triangles (marker 0)
    for (int fi = 0; fi < M; ++fi)
    {
        tetgenio::facet &fac = in.facetlist[fi];
        fac.numberofholes = 0;
        fac.holelist = nullptr;
        fac.numberofpolygons = 1;
        fac.polygonlist = new tetgenio::polygon[1];
        tetgenio::polygon &poly = fac.polygonlist[0];
        poly.numberofvertices = 3;
        poly.vertexlist = new int[3];
        poly.vertexlist[0] = F(fi, 0);
        poly.vertexlist[1] = F(fi, 1);
        poly.vertexlist[2] = F(fi, 2);
        int marker_value = -1;
        if (mesh_facet_marker_ptr) {
            const int raw_marker = mesh_facet_marker_ptr[fi];
            marker_value = (raw_marker < 0) ? -1 : (raw_marker + 1);
        }
        in.facetmarkerlist[fi] = marker_value;
    }

    // Boundary polygons (marker 1..B)
    for (int bi = 0; bi < B; ++bi)
    {
        tetgenio::facet &fac = in.facetlist[M + bi];
        fac.numberofholes = 0;
        fac.holelist = nullptr;
        fac.numberofpolygons = 1;
        fac.polygonlist = new tetgenio::polygon[1];
        tetgenio::polygon &poly = fac.polygonlist[0];
        const auto &loop = boundary_facets[bi];
        poly.numberofvertices = static_cast<int>(loop.size());
        poly.vertexlist = new int[poly.numberofvertices];
        for (int j = 0; j < poly.numberofvertices; ++j) poly.vertexlist[j] = loop[j];
        in.facetmarkerlist[M + bi] =  - (bi + 2);
    }

    // Build switch buffer (NUL-terminated)
    std::vector<char> sw;
    if (py::isinstance<py::str>(tetgen_switches) || py::isinstance<py::bytes>(tetgen_switches))
    {
        std::string s = py::cast<std::string>(tetgen_switches);
        sw.assign(s.begin(), s.end());
        sw.push_back('\0');
    }
    else if (py::isinstance<py::array>(tetgen_switches))
    {
        py::array_t<uint8_t, py::array::c_style | py::array::forcecast> a = tetgen_switches;
        auto r = a.unchecked<1>();
        sw.resize(r.shape(0) + 1);
        for (ssize_t i = 0; i < r.shape(0); ++i) sw[i] = static_cast<char>(r(i));
        sw.back() = '\0';
    }
    else
    {
        throw std::runtime_error("tetgen_switches must be str, bytes, or 1D byte array");
    }
    // Ensure neighbors are requested if boundary faces are needed
    if (compute_boundary_faces) {
        bool has_n = false;
        bool has_f = false;
        for (char c : sw) {
            if (c == '\0') break;
            if (c == 'n') has_n = true;
            if (c == 'f') has_f = true;
        }
        if (!has_n || !has_f) {
            if (!sw.empty() && sw.back() == '\0') sw.pop_back();
            if (!has_n) sw.push_back('n');
            if (!has_f) sw.push_back('f');
            sw.push_back('\0');
        }
    }


    // Tetrahedralize
    tetrahedralize(sw.data(), &in, &out);

    // Populate result
    TetwrapIO res;
    res.points   = to_array_f64(out.pointlist, out.numberofpoints, 3);
    res.tets     = to_array_i32(out.tetrahedronlist, out.numberoftetrahedra, out.numberofcorners);
    res.corners  = out.numberofcorners;
    // reconstruct switch string if provided as array
    if (py::isinstance<py::str>(tetgen_switches)) res.switches = py::cast<std::string>(tetgen_switches);
    else res.switches = ""; // optional

    // Faces (-f)
    if (out.numberoftrifaces > 0 && out.trifacelist) {
        res.tri_faces = to_array_i32(out.trifacelist, out.numberoftrifaces, 3);
        if (out.trifacemarkerlist)
            res.tri_markers = to_vector_i32(out.trifacemarkerlist, out.numberoftrifaces);
        else
            res.tri_markers = py::none();
    } else {
        res.tri_faces   = py::none();
        res.tri_markers = py::none();
    }
    std::map<std::array<int, 3>, int> triface_marker_map;
    if (out.numberoftrifaces > 0 && out.trifacelist && out.trifacemarkerlist) {
        for (int i = 0; i < out.numberoftrifaces; ++i) {
            std::array<int, 3> key = {
                out.trifacelist[3 * i + 0],
                out.trifacelist[3 * i + 1],
                out.trifacelist[3 * i + 2]
            };
            std::sort(key.begin(), key.end());
            triface_marker_map[key] = out.trifacemarkerlist[i];
        }
    }

    // Edges (-e)
    if (out.numberofedges > 0 && out.edgelist) {
        res.edges = to_array_i32(out.edgelist, out.numberofedges, 2);
        if (out.edgemarkerlist)
            res.edge_markers = to_vector_i32(out.edgemarkerlist, out.numberofedges);
        else
            res.edge_markers = py::none();
    } else {
        res.edges        = py::none();
        res.edge_markers = py::none();
    }

    // Neighbors (-n)
    if (out.neighborlist)
        res.neighbors = to_array_i32(out.neighborlist, out.numberoftetrahedra, 4);
    else
        res.neighbors = py::none();

    if (compute_boundary_faces && !res.neighbors.is_none()) {
        py::array_t<int> boundary_faces =
            compute_boundary_face_tris(
                res.tets.cast<py::array_t<int>>(),
                res.neighbors.cast<py::array_t<int>>());
        res.boundary_tri_faces = boundary_faces;

        if (!triface_marker_map.empty()) {
            auto faces = boundary_faces.unchecked<2>();
            py::array_t<int> boundary_markers({faces.shape(0)});
            auto markers = boundary_markers.mutable_unchecked<1>();
            for (ssize_t i = 0; i < faces.shape(0); ++i) {
                std::array<int, 3> key = {faces(i, 0), faces(i, 1), faces(i, 2)};
                std::sort(key.begin(), key.end());
                auto it = triface_marker_map.find(key);
                markers(i) = (it != triface_marker_map.end()) ? it->second : 0;
            }
            res.boundary_tri_markers = boundary_markers;
        } else {
            res.boundary_tri_markers = py::none();
        }
    } else {
        res.boundary_tri_faces = py::none();
        res.boundary_tri_markers = py::none();
    }
    // Point markers
    if (out.pointmarkerlist)
        res.point_markers = to_vector_i32(out.pointmarkerlist, out.numberofpoints);
    else
        res.point_markers = py::none();

    // Attributes (-A with regions)
    if (out.tetrahedronattributelist && out.numberoftetrahedronattributes > 0)
        res.tet_attr = to_array_f64(out.tetrahedronattributelist, out.numberoftetrahedra, out.numberoftetrahedronattributes);
    else
        res.tet_attr = py::none();

    // Volumes (if present)
    if (out.tetrahedronvolumelist)
        res.tet_vol = to_vector_f64(out.tetrahedronvolumelist, out.numberoftetrahedra);
    else
        res.tet_vol = py::none();

    return res;
}


PYBIND11_MODULE(_tetwrap, m)
{
    // Expose rich result class
    py::class_<TetwrapIO>(m, "TetwrapIO")
        .def_readonly("points", &TetwrapIO::points)
        .def_readonly("tets", &TetwrapIO::tets)
        .def_readonly("tri_faces", &TetwrapIO::tri_faces)
        .def_readonly("tri_markers", &TetwrapIO::tri_markers)
        .def_readonly("boundary_tri_faces", &TetwrapIO::boundary_tri_faces)
        .def_readonly("boundary_tri_markers", &TetwrapIO::boundary_tri_markers)
        .def_readonly("edges", &TetwrapIO::edges)
        .def_readonly("edge_markers", &TetwrapIO::edge_markers)
        .def_readonly("neighbors", &TetwrapIO::neighbors)
        .def_readonly("point_markers", &TetwrapIO::point_markers)
        .def_readonly("tet_attr", &TetwrapIO::tet_attr)
        .def_readonly("tet_vol", &TetwrapIO::tet_vol)
        .def_readonly("corners", &TetwrapIO::corners)
        .def_readonly("switches", &TetwrapIO::switches);

    // Back-compat: return (points, tets)
    m.def("build_volume_mesh",
          [](py::array_t<double, py::array::c_style | py::array::forcecast> vertices,
             py::array_t<int,    py::array::c_style | py::array::forcecast> mesh_facets,
             const std::vector<std::vector<int>> &boundary_facets,
             py::object tetgen_switches) {
                TetwrapIO io = tetrahedralize_core(vertices, mesh_facets, py::none(), boundary_facets, tetgen_switches);
                return std::make_pair(io.points.cast<py::array_t<double>>(), io.tets.cast<py::array_t<int>>());
          },
          py::arg("vertices"),
          py::arg("mesh_facets"),
          py::arg("boundary_facets"),
          py::arg("tetgen_switches"),
          R"pbdoc(
              Build a TetGen volume mesh from a surface PLC and return (points, tets).
          )pbdoc");

    
    m.def("_tetrahedralize",
          &tetrahedralize_core,
          py::arg("vertices"),
          py::arg("mesh_facets"),
          py::arg("mesh_facet_markers") = py::none(),
          py::arg("boundary_facets"),
          py::arg("tetgen_switches"),
          py::arg("compute_boundary_faces") = true,
          R"pbdoc(
              Build a TetGen volume mesh and return a TetwrapIO object.
              Use TetGen switches to request faces (-f), edges (-e), neighbors (-n).
          )pbdoc");
}
