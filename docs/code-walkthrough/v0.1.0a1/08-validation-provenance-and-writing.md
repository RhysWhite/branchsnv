# 08 — Cross-input validation, provenance, and output writing

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `src/branchsnv/validation.py`, `src/branchsnv/provenance.py`, `src/branchsnv/writing.py`  
**Last checked against source:** 5 August 2026

This chapter covers exact taxon compatibility, deterministic report construction, TSV/JSON serialisation, and temporary-file staging.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Compatibility record and validation: `validation.py`, lines 1–44

```python
 1  """Cross-input validation helpers."""
 2  
 3  from __future__ import annotations
 4  
 5  from dataclasses import dataclass
 6  
 7  from .errors import ValidationError
 8  from .models import Alignment, Tree
 9  
10  
11  @dataclass(frozen=True)
12  class Compatibility:
13      alignment_taxa: int
14      tree_tips: int
15      matched_taxa: int
16      alignment_only: tuple[str, ...]
17      tree_only: tuple[str, ...]
18  
19  
20  def validate_compatibility(alignment: Alignment, tree: Tree) -> Compatibility:
21      alignment_names = set(alignment.taxa)
22      tree_names = {tip.name for tip in tree.tips()}
23      alignment_only = tuple(sorted(alignment_names - tree_names))
24      tree_only = tuple(sorted(tree_names - alignment_names))
25      if alignment_only or tree_only:
26          parts: list[str] = []
27          if alignment_only:
28              parts.append(
29                  "alignment-only: " + ", ".join(alignment_only[:10])
30                  + (f" (and {len(alignment_only) - 10} more)" if len(alignment_only) > 10 else "")
31              )
32          if tree_only:
33              parts.append(
34                  "tree-only: " + ", ".join(tree_only[:10])
35                  + (f" (and {len(tree_only) - 10} more)" if len(tree_only) > 10 else "")
36              )
37          raise ValidationError("Tree and alignment taxon sets differ (" + "; ".join(parts) + ").")
38      return Compatibility(
39          alignment_taxa=alignment.ntax,
40          tree_tips=len(tree_names),
41          matched_taxa=len(tree_names),
42          alignment_only=alignment_only,
43          tree_only=tree_only,
44      )
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1–8 | Docstring and imports. | `ValidationError` is shared with CLI safety checks. |
| 11–17 | Defines immutable `Compatibility` counts and mismatch tuples. | On success, mismatch tuples are empty; record is returned for reporting to `validate`. |
| 20 | Defines exact compatibility check. | It does not reorder either input. |
| 21 | Converts alignment taxa to set. | NEXUS parser has already rejected duplicates. |
| 22 | Converts tree tip names to set. | Newick parser has already required names and rejected duplicates. |
| 23–24 | Computes sorted alignment-only and tree-only names. | Deterministic diagnostics. |
| 25 | Enters error construction when either side differs. | Exact set equality is required. |
| 26 | Starts message-part list. | Allows one-sided or two-sided mismatch. |
| 27–31 | Adds alignment-only preview up to ten plus omitted count. | Full mismatch still rejected. |
| 32–36 | Adds tree-only preview similarly. | Semicolon separates categories. |
| 37 | Raises `ValidationError`. | No taxon intersection/subsetting is performed. |
| 38–44 | Returns counts and empty mismatch tuples on success. | `matched_taxa` equals tree-tip count; with exact sets, also alignment taxon count. |

**Protected by:** `ValidationTests.test_rejects_taxon_set_mismatch` and successful CLI validation.

## `build_report`: `provenance.py`, lines 1–90

```python
 1  """Deterministic provenance report construction."""
 2  
 3  from __future__ import annotations
 4  
 5  from pathlib import Path
 6  from typing import Any
 7  
 8  from . import __version__
 9  from .analysis import AnalysisSummary
10  from .models import Alignment, BranchRecord, Tree
11  from .util import sha256_file, sha256_lines
12  
13  
14  def build_report(
15      *,
16      alignment: Alignment,
17      alignment_path: Path,
18      tree: Tree,
19      tree_path: Path,
20      branch: BranchRecord,
21      rooting: dict[str, Any],
22      selector: dict[str, Any],
23      mode: str,
24      include_ambiguous: bool,
25      summary: AnalysisSummary,
26      results_path: Path,
27      members_path: Path,
28      results_hash_path: Path | None = None,
29      members_hash_path: Path | None = None,
30  ) -> dict[str, Any]:
31      return {
32          "schema_version": 1,
33          "tool": {"name": "BRANCHSNV", "version": __version__},
34          "inputs": {
35              "alignment": {
36                  "name": alignment_path.name,
37                  "sha256": sha256_file(alignment_path),
38                  "ntax": alignment.ntax,
39                  "nchar": alignment.nchar,
40                  "format": "transposed_nexus",
41                  "gap_symbol": alignment.gap,
42                  "missing_symbol": alignment.missing,
43              },
44              "tree": {
45                  "name": tree_path.name,
46                  "sha256": sha256_file(tree_path),
47                  "tips": len(tree.tips()),
48                  "format": "newick",
49              },
50          },
51          "rooting": rooting,
52          "branch": {
53              "branch_id": branch.branch_id,
54              "short_id": branch.short_id,
55              "descendant_count": branch.descendant_count,
56              "descendant_taxa_sha256": sha256_lines(branch.descendant_tips),
57              "selection": selector,
58          },
59          "parameters": {
60              "mode": mode,
61              "include_ambiguous_parsimony_sites": include_ambiguous,
62              "state_cost_model": "unordered_equal_cost",
63              "gap_treatment": "unknown_state",
64              "missing_treatment": "unknown_state",
65              "fixed_exclusive_descendant_call_rate": 1.0,
66              "fixed_exclusive_outside_call_rate": 1.0,
67          },
68          "results": {
69              "sites_examined": summary.sites_examined,
70              "reported_sites": summary.reported_sites,
71              "fixed_exclusive_sites": summary.fixed_exclusive_sites,
72              "parsimony": {
73                  "unambiguous_change": summary.unambiguous_change_sites,
74                  "change_state_ambiguous": summary.change_state_ambiguous_sites,
75                  "placement_ambiguous": summary.placement_ambiguous_sites,
76                  "no_change": summary.no_change_sites,
77              },
78          },
79          "outputs": {
80              "results_tsv": {
81                  "name": results_path.name,
82                  "sha256": sha256_file(results_hash_path or results_path),
83              },
84              "branch_members": {
85                  "name": members_path.name,
86                  "sha256": sha256_file(members_hash_path or members_path),
87              },
88          },
89          "warnings": [],
90      }
```

### Signature: lines 1–30

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1–11 | Docstring and imports. | Report uses package version and SHA utilities. |
| 14–30 | Defines keyword-only report builder and optional alternate hash paths. | Keyword-only `*` reduces accidental argument-order mistakes. Staged output paths can be hashed while final names are reported. |

### Report object: lines 31–90

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 31 | Returns one nested dictionary literal. | No timestamp or random identifier is introduced. |
| 32 | Sets schema version 1. | JSON Schema tests target this constant. |
| 33 | Records tool name and imported version. | Version agreement is separately tested. |
| 34–43 | Records alignment basename, byte hash, dimensions, format label, gap, and missing symbol. | Absolute path is omitted; original file bytes are hashed. |
| 44–49 | Records tree basename, byte hash, rooted tree tip count, and format label. | Hash is of original Newick file, while count is from rooted/cloned tree. |
| 51 | Embeds rooting metadata produced by CLI. | May include sorted outgroup and source-file hash. |
| 52–58 | Records branch full/short ID, descendant count, hash of sorted descendant names, and selector metadata. | Branch ID should equal `b_` plus membership hash. |
| 59–67 | Records mode, ambiguity flag, cost model, gap/missing treatment, and strict call-rate thresholds. | These values make core assumptions machine-readable. |
| 68–78 | Records examined/reported counts, strict marker count, and all four parsimony status totals. | Status totals include rows not reported. |
| 79–87 | Records final output basenames and hashes of staged-or-final result/member files. | Report itself is not listed or hashed, avoiding self-reference. |
| 89 | Emits an empty warnings list. | Deterministic placeholder for schema-compatible future warnings. |
| 90 | Closes returned dictionary. | Writer handles serialisation. |

**Protected by:** `ProvenanceTests.test_report_is_internally_consistent` and schema test.

## Output field contracts: `writing.py`, lines 1–47

```python
 1  """Deterministic, atomic output writing."""
 2  
 3  from __future__ import annotations
 4  
 5  import csv
 6  import json
 7  import os
 8  import tempfile
 9  from pathlib import Path
10  from typing import Any
11  
12  from .errors import ValidationError
13  from .models import BranchRecord, SiteResult
14  from .util import bool_text
15  
16  _TSV_FIELDS = (
17      "site_id",
18      "reference",
19      "position",
20      "input_row",
21      "parent_states",
22      "child_states",
23      "possible_pairs",
24      "change",
25      "parsimony_status",
26      "fixed_within_clade",
27      "exclusive_to_clade",
28      "descendant_state",
29      "descendant_total",
30      "descendant_callable",
31      "descendant_state_count",
32      "outside_total",
33      "outside_callable",
34      "outside_same_state_count",
35      "parsimony_score",
36      "selection_reason",
37  )
38  
39  _BRANCH_FIELDS = (
40      "branch_id",
41      "short_id",
42      "descendant_count",
43      "parent_label",
44      "child_label",
45      "first_descendant",
46      "last_descendant",
47  )
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1–14 | Docstring and imports. | `csv`/`json` serialise; `os`/`tempfile` stage; `bool_text` normalises TSV booleans. |
| 16–37 | Defines exact results TSV column order. | Writer and downstream workflows rely on this stable sequence. |
| 39–47 | Defines exact branch inspection TSV column order. | Only first/last descendant are included as previews; full membership is represented by branch ID and can be selected. |

## `AtomicOutputSet`: lines 50–87

```python
50  class AtomicOutputSet:
51      """Stage several files and replace all targets only after every write succeeds."""
52  
53      def __init__(self, targets: list[Path], force: bool = False):
54          self.targets = targets
55          self.force = force
56          self.temporary: dict[Path, Path] = {}
57  
58      def __enter__(self) -> "AtomicOutputSet":
59          canonical = [path.resolve() for path in self.targets]
60          duplicates = [path for path in canonical if canonical.count(path) > 1]
61          if duplicates:
62              raise ValidationError(f"Output paths must be distinct: {duplicates[0]}.")
63          for target in self.targets:
64              if target.exists() and not self.force:
65                  raise ValidationError(f"Output already exists: {target}. Use --force to replace it.")
66              target.parent.mkdir(parents=True, exist_ok=True)
67              descriptor, name = tempfile.mkstemp(
68                  prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
69              )
70              os.close(descriptor)
71              self.temporary[target] = Path(name)
72          return self
73  
74      def staged_path(self, target: Path) -> Path:
75          return self.temporary[target]
76  
77      def commit(self) -> None:
78          for target in self.targets:
79              os.replace(self.temporary[target], target)
80          self.temporary.clear()
81  
82      def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
83          for path in self.temporary.values():
84              try:
85                  path.unlink()
86              except FileNotFoundError:
87                  pass
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 50–51 | Defines staging manager and its intended contract. | “Atomic” is exact per individual `os.replace`; multi-file commit limitations are documented in chapter 10. |
| 53–56 | Stores target order, force policy, and empty target→temporary map. | Target order determines commit order. |
| 58 | Context entry returns self after setup. | Setup exceptions occur before a context is fully entered. |
| 59 | Resolves target paths. | Used to detect aliases. |
| 60 | Finds canonical paths occurring more than once. | O(n²) counting is negligible for one or three outputs. |
| 61–62 | Rejects duplicate outputs. | Prevents two logical outputs sharing one final path. |
| 63 | Iterates targets. | Existing-output checks and temp creation currently interleave. |
| 64–65 | Rejects an existing target unless `force=True`. | Existing content remains untouched. |
| 66 | Creates parent directories recursively. | Output directories need not pre-exist. |
| 67–69 | Creates an empty uniquely named temporary file in the target directory. | Same-directory placement enables atomic replacement on the same filesystem. |
| 70 | Closes low-level descriptor. | Writers reopen by path using text settings. |
| 71 | Stores temporary path. | Later accessed by exact target key. |
| 72 | Returns transaction. | Writers can now run. |
| 74–75 | Returns staged path for a target. | A nonmember key raises `KeyError`. |
| 77–80 | Sequentially replaces each target with its temporary file, then clears map. | `os.replace` overwrites atomically per target; clearing prevents cleanup from removing committed files. |
| 82–87 | On context exit, attempts to delete every remaining temporary path; ignores already-missing files. | Cleans up after writer exceptions or after a partial commit to the extent paths remain. |

## Results, members, report, and branch writers: lines 90–161

```python
 90  def write_results(path: Path, results: tuple[SiteResult, ...]) -> None:
 91      with path.open("w", encoding="utf-8", newline="") as handle:
 92          writer = csv.DictWriter(
 93              handle,
 94              fieldnames=_TSV_FIELDS,
 95              delimiter="\t",
 96              lineterminator="\n",
 97          )
 98          writer.writeheader()
 99          for item in results:
100              writer.writerow(
101                  {
102                      "site_id": item.site_id,
103                      "reference": item.reference,
104                      "position": "" if item.position is None else item.position,
105                      "input_row": item.input_row,
106                      "parent_states": item.parent_states,
107                      "child_states": item.child_states,
108                      "possible_pairs": item.possible_pairs,
109                      "change": item.change,
110                      "parsimony_status": item.parsimony_status,
111                      "fixed_within_clade": bool_text(item.fixed_within_clade),
112                      "exclusive_to_clade": bool_text(item.exclusive_to_clade),
113                      "descendant_state": item.descendant_state,
114                      "descendant_total": item.descendant_total,
115                      "descendant_callable": item.descendant_callable,
116                      "descendant_state_count": item.descendant_state_count,
117                      "outside_total": item.outside_total,
118                      "outside_callable": item.outside_callable,
119                      "outside_same_state_count": item.outside_same_state_count,
120                      "parsimony_score": item.parsimony_score,
121                      "selection_reason": item.selection_reason,
122                  }
123              )
124  
125  
126  def write_members(path: Path, branch: BranchRecord) -> None:
127      with path.open("w", encoding="utf-8", newline="\n") as handle:
128          handle.write("".join(f"{name}\n" for name in branch.descendant_tips))
129  
130  
131  def write_report(path: Path, report: dict[str, Any]) -> None:
132      with path.open("w", encoding="utf-8", newline="\n") as handle:
133          handle.write(
134              json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
135          )
136  
137  
138  def write_branches(path: Path, branches: list[BranchRecord]) -> None:
139      with path.open("w", encoding="utf-8", newline="") as handle:
140          writer = csv.DictWriter(
141              handle,
142              fieldnames=_BRANCH_FIELDS,
143              delimiter="\t",
144              lineterminator="\n",
145          )
146          writer.writeheader()
147          for branch in sorted(
148              branches,
149              key=lambda item: (-item.descendant_count, item.descendant_tips, item.branch_id),
150          ):
151              writer.writerow(
152                  {
153                      "branch_id": branch.branch_id,
154                      "short_id": branch.short_id,
155                      "descendant_count": branch.descendant_count,
156                      "parent_label": branch.parent_label,
157                      "child_label": branch.child_label,
158                      "first_descendant": branch.descendant_tips[0],
159                      "last_descendant": branch.descendant_tips[-1],
160                  }
161              )
```

### `write_results`: lines 90–123

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 90 | Declares writer for immutable result tuple. | Used on a staged path. |
| 91 | Opens UTF-8 text with `newline=""`. | Lets `csv` control line endings. |
| 92–97 | Creates tab-delimited `DictWriter` with fixed fields and `\n`. | Cross-platform LF output. |
| 98 | Writes header row. | Empty result sets still produce a valid header-only TSV. |
| 99 | Iterates results in supplied order. | Analysis already sorts by input row. |
| 100–123 | Writes one dictionary row, using blank for absent numeric position and lowercase text for booleans. | Strings containing tabs/newlines would be CSV-quoted according to the standard library. |

### `write_members`: lines 126–128

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 126 | Declares member writer. | Branch descendants are already sorted. |
| 127 | Opens UTF-8 with LF newline. | Cross-platform bytes. |
| 128 | Builds and writes one terminal-newline line per descendant. | Empty branches cannot occur for a non-root node. |

### `write_report`: lines 131–135

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 131 | Declares JSON writer. | Receives already-built dictionary. |
| 132 | Opens UTF-8 with LF newline. | Stable line endings. |
| 133–135 | Serialises with sorted keys, two-space indentation, Unicode preserved, and one terminal newline. | Deterministic key ordering and human-readable output. |

### `write_branches`: lines 138–161

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 138 | Declares branch table writer. | Consumes list from `branch_records`. |
| 139–145 | Opens output and creates tab writer with LF. | Same deterministic TSV settings as results. |
| 146 | Writes header. | Always present. |
| 147–150 | Sorts branches by descending descendant count, then descendant tuple, then branch ID. | Larger clades appear first; ties are deterministic. |
| 151–160 | Writes IDs, count, labels, and first/last sorted descendant. | First/last are safe because every non-root branch has at least one descendant tip. |
| 161 | Closes dictionary/call. | File closes when context exits. |

## Output invariants

- All committed text outputs use UTF-8 and LF.
- Results and branch tables always include headers.
- JSON key order, indentation, and terminal newline are fixed.
- Final output basenames—not absolute paths—are stored in provenance.
- Result/member hashes describe exact committed bytes because staging files are not modified between hashing and replacement.
