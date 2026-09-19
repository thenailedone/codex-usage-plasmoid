#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
package_dir="$project_dir/package"
version="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["KPlugin"]["Version"])' "$package_dir/metadata.json")"
archive="$project_dir/dist/codex-usage-$version.plasmoid"

python3 -m json.tool "$package_dir/metadata.json" >/dev/null
python3 -m unittest discover -s "$project_dir/tests" -v
mkdir -p "$project_dir/dist"
rm -f "$archive"
(cd "$package_dir" && zip -qr "$archive" . -x '*/__pycache__/*' '*.pyc')
printf '%s\n' "$archive"
