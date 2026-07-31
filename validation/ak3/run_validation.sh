#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 ALIGNMENT.nex TREE.nwk" >&2
  exit 2
fi

alignment=$1
tree=$2
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

expected_alignment_sha="40c49b026c52e04530ecbbee7044567ac3355eccf7adda42a7d96bf977df9014"
expected_tree_sha="18322b2808baf621d09dd5292027205e68a0f207d7be44f043bd044d0d314bd0"

sha256_file() {
  python - "$1" <<'PY'
import hashlib
import sys
from pathlib import Path
path = Path(sys.argv[1])
digest = hashlib.sha256()
with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
PY
}

observed_alignment_sha=$(sha256_file "$alignment")
observed_tree_sha=$(sha256_file "$tree")

[[ "$observed_alignment_sha" == "$expected_alignment_sha" ]] || {
  echo "Alignment checksum mismatch." >&2
  exit 1
}
[[ "$observed_tree_sha" == "$expected_tree_sha" ]] || {
  echo "Tree checksum mismatch." >&2
  exit 1
}

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

branchsnv validate \
  --alignment "$alignment" \
  --tree "$tree" \
  --outgroup SRR13968194

branchsnv find \
  --alignment "$alignment" \
  --tree "$tree" \
  --outgroup SRR13968194 \
  --clade-tips "$script_dir/sapi_385_tips.txt" \
  --mode both \
  --output "$workdir/sapi.tsv" \
  --members-output "$workdir/sapi.members.txt" \
  --report "$workdir/sapi.report.json"

branchsnv find \
  --alignment "$alignment" \
  --tree "$tree" \
  --outgroup SRR13968194 \
  --clade-tips "$script_dir/mrsa_360_tips.txt" \
  --mode both \
  --output "$workdir/mrsa.tsv" \
  --members-output "$workdir/mrsa.members.txt" \
  --report "$workdir/mrsa.report.json"

cmp "$workdir/sapi.tsv" "$script_dir/expected/sapi_385_results.tsv"
cmp "$workdir/mrsa.tsv" "$script_dir/expected/mrsa_360_results.tsv"

echo "AK3 validation passed."
