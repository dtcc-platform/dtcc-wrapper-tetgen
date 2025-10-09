#!/usr/bin/env bash
set -euo pipefail

TETGEN_VERSION="${TETGEN_VERSION:-v1.5.0}"
TETGEN_URL="https://codeberg.org/TetGen/TetGen/archive/${TETGEN_VERSION}.tar.gz"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}" && pwd)"

TARGET_DIR="${REPO_ROOT}/src/dtcc_wrapper_tetgen/cpp/tetgen"

mkdir -p "${TARGET_DIR}"
tmp_tar="$(mktemp)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}" "${tmp_tar}"' EXIT

echo "Downloading ${TETGEN_URL}"
curl -L --fail "${TETGEN_URL}" -o "${tmp_tar}"

echo "Extracting into ${TARGET_DIR}"
tar -xzf "${tmp_tar}" -C "${tmp_dir}"
src_dir="$(find "${tmp_dir}" -mindepth 1 -maxdepth 1 -type d | head -n1)"
if [[ -z "${src_dir}" ]]; then
  echo "Unable to locate extracted TetGen directory" >&2
  exit 1
fi

rsync -a --delete "${src_dir}/" "${TARGET_DIR}/"
echo "TetGen sources refreshed in ${TARGET_DIR}"