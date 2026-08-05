# 01 — Entry points and command-line interface

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `pyproject.toml`, `src/branchsnv/__init__.py`, `src/branchsnv/__main__.py`, `src/branchsnv/cli.py`  
**Last checked against source:** 5 August 2026

This chapter follows execution from installation metadata through argument parsing, command dispatch, and expected error handling.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Packaging entry point: `pyproject.toml`, lines 45–46

```toml
45  [project.scripts]
46  branchsnv = "branchsnv.cli:main"
```

| Line(s) | Literal effect | Why it matters |
|---|---|---|
| 45 | Opens the `[project.scripts]` table. | Packaging tools use this table to create shell commands. |
| 46 | Installs a command named `branchsnv` that imports `branchsnv.cli` and calls `main`. | The installed executable and the Python API share one dispatcher. |

Pinned source: [`pyproject.toml` lines 45–46](https://github.com/RhysWhite/branchsnv/blob/582d3883d39adb8c591d9eb152143227c9696eec/pyproject.toml#L45-L46).

## Package version: `__init__.py`, lines 1–3

```python
1  """BRANCHSNV package."""
2  
3  __version__ = "0.1.0a1"
```

| Line(s) | Literal effect | Notes |
|---|---|---|
| 1 | Defines the module docstring. | No analytical effect. |
| 2 | Blank separator. | Formatting only. |
| 3 | Binds `branchsnv.__version__` to `"0.1.0a1"`. | Imported by the CLI and provenance report; release tests compare it with `pyproject.toml` and `CITATION.cff`. |

## Module execution: `__main__.py`, lines 1–3

```python
1  from .cli import main
2  
3  raise SystemExit(main())
```

| Line(s) | Literal effect | Notes |
|---|---|---|
| 1 | Imports `main` from the sibling `cli` module. | Used by `python -m branchsnv`. |
| 2 | Blank separator. | Formatting only. |
| 3 | Calls `main()`, then raises `SystemExit` with its integer return value. | Converts `0`, `1`, or `2` into an operating-system process status. Unexpected exceptions are not hidden. |

## Module header and imports: `cli.py`, lines 1–32

```python
 1  """Command-line interface for BRANCHSNV."""
 2  
 3  from __future__ import annotations
 4  
 5  import argparse
 6  import sys
 7  from collections import Counter
 8  from pathlib import Path
 9  
10  from . import __version__
11  from .analysis import analyse_branch
12  from .errors import BranchSNVError, SelectionError, ValidationError
13  from .models import BranchRecord, Tree
14  from .newick import (
15      branch_records,
16      read_newick,
17      reroot_on_outgroup,
18      resolve_branch_id,
19      select_exact_descendants,
20      select_mrca_branch,
21  )
22  from .nexus import read_transposed_nexus
23  from .provenance import build_report
24  from .validation import validate_compatibility
25  from .util import sha256_file
26  from .writing import (
27      AtomicOutputSet,
28      write_branches,
29      write_members,
30      write_report,
31      write_results,
32  )
```

| Line(s) | Literal effect | Why it exists |
|---|---|---|
| 1 | Module docstring. | Identifies this file as the CLI layer. |
| 3 | Postpones evaluation of annotations. | Allows modern annotations without forcing all referenced types to be resolved immediately. |
| 5–8 | Imports `argparse`, `sys`, `Counter`, and `Path`. | Argument parsing, stderr output, duplicate detection, and filesystem paths. |
| 10 | Imports the package version. | Powers `--version` and keeps version reporting centralised. |
| 11 | Imports the core branch-analysis function. | This is the scientific work invoked by `find`. |
| 12–13 | Imports expected exceptions and tree/branch models. | Expected failures become concise user-facing errors; models support annotations. |
| 14–21 | Imports Newick/tree operations. | Parsing, rooting, listing, resolving, and selecting branches. |
| 22–25 | Imports NEXUS parsing, report construction, compatibility validation, and hashing. | Connects input, validation, and provenance layers. |
| 26–32 | Imports the atomic output transaction and four writers. | Prevents handlers from implementing file formats themselves. |

### Design boundary

`cli.py` coordinates modules but does not implement NEXUS parsing, tree algorithms, parsimony, or TSV formatting. This separation makes those components independently testable.

## `_read_name_file`: lines 35–51

```python
35  def _read_name_file(path: Path) -> set[str]:
36      try:
37          lines = path.read_text(encoding="utf-8-sig").splitlines()
38      except OSError as exc:
39          raise SelectionError(f"Could not read taxon list {path}: {exc}") from exc
40      names: list[str] = []
41      for line_number, line in enumerate(lines, start=1):
42          value = line.strip()
43          if not value or value.startswith("#"):
44              continue
45          names.append(value)
46      if not names:
47          raise SelectionError(f"Taxon list {path} contains no names.")
48      duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
49      if duplicates:
50          raise SelectionError(f"Taxon list contains duplicate name(s): {', '.join(duplicates[:10])}.")
51      return set(names)
```

**Input:** a `Path` to a one-name-per-line file.  
**Return:** a `set[str]` containing unique non-comment names.  
**Used for:** `--outgroup-file` and `--clade-tips`.

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 35 | Defines the private helper and its return type. | The leading underscore marks it as internal. |
| 36–39 | Reads the entire file as UTF-8 with optional BOM removal; wraps `OSError` as `SelectionError`. | Users see the path and original I/O reason without a traceback. |
| 40 | Creates a list rather than a set. | Repeated names must remain visible until duplicate checking is complete. |
| 41 | Iterates over lines with one-based numbers. | `line_number` is currently unused; it could support future line-specific diagnostics. |
| 42 | Removes leading and trailing whitespace. | Indented names and trailing spaces normalise to the same exact taxon string. |
| 43–44 | Skips empty lines and lines whose first non-space character is `#`. | Supports readable comment-bearing lists. Inline comments are not stripped. |
| 45 | Appends each accepted name. | Names remain case-sensitive. |
| 46–47 | Rejects empty or comment-only files. | Avoids an empty branch or outgroup request. |
| 48 | Counts names, keeps those seen more than once, and sorts them. | Sorting makes the error deterministic. |
| 49–50 | Rejects duplicates and displays up to ten names. | Prevents a misleading file from silently collapsing to a set. |
| 51 | Converts the validated list to a set. | Downstream operations need membership, not file order. |

**Protected directly by:** no dedicated unit test for comments/duplicates in name files in this commit; successful `--clade-tips` use is exercised by CLI and provenance tests. This is recorded as a test gap in chapter 09.

## `_add_rooting_arguments`: lines 54–71

```python
54  def _add_rooting_arguments(parser: argparse.ArgumentParser) -> None:
55      group = parser.add_mutually_exclusive_group(required=True)
56      group.add_argument(
57          "--outgroup",
58          nargs="+",
59          metavar="TIP",
60          help="Root on the edge separating these monophyletic outgroup tips.",
61      )
62      group.add_argument(
63          "--outgroup-file",
64          type=Path,
65          help="File containing one outgroup tip name per line.",
66      )
67      group.add_argument(
68          "--accept-existing-root",
69          action="store_true",
70          help="Use the root encoded by the Newick topology without rerooting.",
71      )
```

| Line(s) | Literal effect | Consequence |
|---|---|---|
| 54 | Defines a parser-mutating helper returning `None`. | Reuses identical rooting options across all three commands. |
| 55 | Creates a required mutually exclusive group. | Exactly one rooting choice must be supplied. |
| 56–61 | Adds `--outgroup TIP [TIP ...]`. | `nargs="+"` requires at least one inline tip. |
| 62–66 | Adds `--outgroup-file PATH`, converted to `Path`. | Existence is checked later when the file is read. |
| 67–71 | Adds Boolean `--accept-existing-root`. | The user must explicitly accept the encoded Newick root rather than receiving an implicit default. |

The mutual exclusion is enforced by `argparse` before BRANCHSNV reads any files. Parser errors therefore raise `SystemExit(2)` outside the `main()` runtime-error `try` block.

## `_root_tree`: lines 74–92

```python
74  def _root_tree(tree: Tree, args: argparse.Namespace) -> tuple[Tree, dict[str, object]]:
75      if args.accept_existing_root:
76          if len(tree.root.children) < 2:
77              raise ValidationError("The existing root must have at least two children.")
78          return tree, {"method": "existing_newick_root", "outgroup": []}
79      if args.outgroup_file:
80          names = _read_name_file(args.outgroup_file)
81          method = "outgroup_file"
82          source = args.outgroup_file.name
83      else:
84          names = set(args.outgroup)
85          method = "outgroup"
86          source = None
87      rooted = reroot_on_outgroup(tree, names)
88      report: dict[str, object] = {"method": method, "outgroup": sorted(names)}
89      if source:
90          report["source"] = source
91          report["source_sha256"] = sha256_file(args.outgroup_file)
92      return rooted, report
```

**Input:** parsed `Tree` plus the command namespace.  
**Return:** `(rooted_tree, rooting_metadata)`.

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 74 | Declares the helper and tuple return type. | Rooting metadata is built at the same time as the rooted topology. |
| 75–78 | If the existing root was accepted, requires at least two root children and returns the same tree object. | This branch does not reinterpret the topology; it records method `existing_newick_root`. |
| 79–82 | For `--outgroup-file`, reads names, records method and only the file basename. | Omitting absolute paths supports deterministic reports across directories. |
| 83–86 | Otherwise converts inline outgroup arguments to a set and records method `outgroup`. | Repeated inline names are silently collapsed in this version, unlike duplicate names in files or `--mrca`. |
| 87 | Calls `reroot_on_outgroup`. | Monophyly, missing names, whole-tree requests, and edge uniqueness are checked in `newick.py`. |
| 88 | Builds metadata with a sorted outgroup list. | Output is independent of command-line or set iteration order. |
| 89–91 | For a source file, records basename and SHA-256. | The report can identify exact outgroup-file content. |
| 92 | Returns rooted tree and metadata. | Downstream selection and parent→child direction use this rooted tree. |

## `_select_branch`: lines 95–113

```python
 95  def _select_branch(tree: Tree, args: argparse.Namespace) -> tuple[BranchRecord, dict[str, object]]:
 96      if args.clade_tips:
 97          requested = _read_name_file(args.clade_tips)
 98          branch = select_exact_descendants(tree, requested)
 99          return branch, {
100              "method": "exact_descendant_file",
101              "source": args.clade_tips.name,
102              "sha256": sha256_file(args.clade_tips),
103          }
104      if args.mrca:
105          requested = set(args.mrca)
106          if len(requested) != len(args.mrca):
107              raise SelectionError("--mrca contains duplicate tip names.")
108          branch = select_mrca_branch(tree, requested)
109          return branch, {"method": "mrca", "tips": sorted(requested)}
110      if args.branch_id:
111          branch = resolve_branch_id(branch_records(tree), args.branch_id)
112          return branch, {"method": "branch_id", "requested": args.branch_id}
113      raise SelectionError("No branch-selection method was supplied.")
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 95 | Defines branch selection, returning a `BranchRecord` and metadata. | Metadata records how the same branch can be traced later. |
| 96–103 | Reads `--clade-tips`, requires an exact descendant set, and hashes the file. | This is the strict publication-oriented selection route. |
| 104–107 | Converts `--mrca` names to a set and explicitly rejects duplicates. | Prevents the apparent number of anchors from differing from the actual set. |
| 108–109 | Selects the incoming branch to the MRCA and records sorted anchors. | Additional descendants under that MRCA are allowed by this method. |
| 110–112 | Lists branches, resolves a full ID or unique prefix, and records the literal request. | Prefix resolution is deterministic but ambiguous prefixes are rejected. |
| 113 | Raises if no method is present. | Defensive for programmatic calls; normal CLI parsing makes this unreachable. |

## `_reject_output_input_collisions`: lines 117–126

```python
117  def _reject_output_input_collisions(
118      outputs: list[Path], inputs: list[Path | None]
119  ) -> None:
120      input_map = {path.resolve(): path for path in inputs if path is not None}
121      for output in outputs:
122          resolved = output.resolve()
123          if resolved in input_map:
124              raise ValidationError(
125                  f"Output path {output} resolves to input path {input_map[resolved]}."
126              )
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 117–119 | Defines a function accepting output paths and optional input paths. | It returns nothing on success. |
| 120 | Resolves every non-`None` input path and maps it to the original spelling. | Resolving catches `.`/`..` aliases and existing symlink aliases. |
| 121–122 | Resolves each output. | Comparison occurs on normalised paths. |
| 123–126 | Rejects an output that resolves to any input. | `--force` cannot be used to overwrite an input file. Separate hard links to the same inode are not detected by pathname resolution. |

**Protected by:** `CliTests.test_refuses_to_overwrite_an_input_even_with_force`.

## `build_parser`: lines 128–192

```python
128  def build_parser() -> argparse.ArgumentParser:
129      parser = argparse.ArgumentParser(
130          prog="branchsnv",
131          description=(
132              "Identify fixed clade-associated nucleotide states and parsimoniously "
133              "reconstructed substitutions on a selected phylogenetic branch."
134          ),
135      )
136      parser.add_argument("--version", action="version", version=f"BRANCHSNV {__version__}")
137      subparsers = parser.add_subparsers(dest="command", required=True)
138  
139      validate_parser = subparsers.add_parser(
140          "validate", help="Validate a transposed NEXUS alignment and rooted Newick tree."
141      )
142      validate_parser.add_argument("--alignment", required=True, type=Path)
143      validate_parser.add_argument("--tree", required=True, type=Path)
144      _add_rooting_arguments(validate_parser)
145  
146      inspect_parser = subparsers.add_parser(
147          "inspect", help="List every non-root branch and its deterministic identifier."
148      )
149      inspect_parser.add_argument("--tree", required=True, type=Path)
150      inspect_parser.add_argument("--output", required=True, type=Path)
151      inspect_parser.add_argument("--force", action="store_true")
152      _add_rooting_arguments(inspect_parser)
153  
154      find_parser = subparsers.add_parser(
155          "find", help="Identify SNVs associated with one selected branch."
156      )
157      find_parser.add_argument("--alignment", required=True, type=Path)
158      find_parser.add_argument("--tree", required=True, type=Path)
159      _add_rooting_arguments(find_parser)
160      selection = find_parser.add_mutually_exclusive_group(required=True)
161      selection.add_argument(
162          "--clade-tips",
163          type=Path,
164          help="File containing the exact descendants of the selected branch.",
165      )
166      selection.add_argument(
167          "--mrca",
168          nargs="+",
169          metavar="TIP",
170          help="Select the branch leading to the MRCA of these tips.",
171      )
172      selection.add_argument(
173          "--branch-id",
174          help="Full deterministic branch identifier or an unambiguous prefix from inspect.",
175      )
176      find_parser.add_argument(
177          "--mode",
178          choices=("fixed-exclusive", "parsimony", "both"),
179          default="both",
180      )
181      find_parser.add_argument(
182          "--include-ambiguous",
183          action="store_true",
184          help="Also report parsimony sites with ambiguous change state or placement.",
185      )
186      find_parser.add_argument("--output", required=True, type=Path, help="Results TSV.")
187      find_parser.add_argument(
188          "--members-output", required=True, type=Path, help="Sorted descendant-tip list."
189      )
190      find_parser.add_argument("--report", required=True, type=Path, help="Provenance JSON.")
191      find_parser.add_argument("--force", action="store_true")
192      return parser
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 128 | Defines parser construction. | A fresh parser is built for every `main()` call, which supports direct unit testing. |
| 129–135 | Creates the top-level parser with program name and scientific description. | Controls top-level help output. |
| 136 | Adds `--version` using the package version. | `argparse` prints and exits immediately. |
| 137 | Creates required subparsers and stores the selected name in `args.command`. | No command is not valid. |
| 139–144 | Defines `validate`, requiring alignment, tree, and one rooting choice. | No branch selector or output file is needed. |
| 146–152 | Defines `inspect`, requiring tree, output, optional `--force`, and rooting. | Branch direction and descendants are root-dependent. |
| 154–159 | Starts `find` and requires alignment, tree, and rooting. | Establishes inputs common to all find routes. |
| 160 | Creates a required mutually exclusive branch-selector group. | Exactly one selector is accepted. |
| 161–165 | Adds exact descendant file selection. | The file is interpreted later by `_read_name_file`. |
| 166–171 | Adds one-or-more MRCA anchor tips. | Selects the branch leading to their MRCA, not necessarily an exact clade equal to the anchor set. |
| 172–175 | Adds deterministic branch ID/prefix selection. | Intended to consume output from `inspect`. |
| 176–180 | Adds `--mode` constrained to three values with default `both`. | Invalid spellings fail before analysis. |
| 181–185 | Adds `--include-ambiguous`. | Changes which ambiguous parsimony rows are reported, not which reconstructions are computed. |
| 186–190 | Requires results, member-list, and provenance-report paths. | A successful `find` always produces all three artifacts. |
| 191 | Adds `--force`. | Existing outputs are otherwise rejected by `AtomicOutputSet`. |
| 192 | Returns the parser. | `main()` then calls `parse_args`. |

## `_run_validate`: lines 195–203

```python
195  def _run_validate(args: argparse.Namespace) -> int:
196      alignment = read_transposed_nexus(args.alignment)
197      tree, rooting = _root_tree(read_newick(args.tree), args)
198      compatibility = validate_compatibility(alignment, tree)
199      print(
200          f"VALID: {compatibility.matched_taxa} taxa, {alignment.nchar} sites; "
201          f"rooting={rooting['method']}."
202      )
203      return 0
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 195 | Defines the `validate` handler. | Returns an integer process code. |
| 196 | Parses and validates the transposed NEXUS alignment. | Produces an immutable `Alignment`. |
| 197 | Parses Newick, then roots it according to the arguments. | Function calls evaluate inside-out. |
| 198 | Requires exact tree-tip/alignment-taxon equality. | Taxon order may differ; names may not. |
| 199–202 | Prints counts and rooting method. | Output is informational; no file is created. |
| 203 | Returns `0`. | Signals success. |

**Protected by:** `CliTests.test_validate` and `ValidationTests.test_rejects_taxon_set_mismatch`.

## `_run_inspect`: lines 206–216

```python
206  def _run_inspect(args: argparse.Namespace) -> int:
207      _reject_output_input_collisions(
208          [args.output], [args.tree, args.outgroup_file]
209      )
210      tree, _rooting = _root_tree(read_newick(args.tree), args)
211      records = branch_records(tree)
212      with AtomicOutputSet([args.output], force=args.force) as transaction:
213          write_branches(transaction.staged_path(args.output), records)
214          transaction.commit()
215      print(f"Wrote {len(records)} branches to {args.output}.")
216      return 0
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 206 | Defines the `inspect` handler. | No alignment is involved. |
| 207–209 | Rejects collision between output and tree/outgroup-file input. | Protects input files before staging. |
| 210 | Parses and roots the tree; deliberately ignores rooting metadata. | `_rooting` naming signals intentional non-use. |
| 211 | Builds one branch record for each non-root node. | Every non-root node has one incoming rooted branch. |
| 212 | Opens an atomic staging context for the output. | Existing output policy and temporary-file creation occur here. |
| 213 | Writes branch records to the staged path. | The final path is untouched until commit. |
| 214 | Replaces the final target. | Uses `os.replace` inside `AtomicOutputSet`. |
| 215 | Prints the count and output path. | Occurs only after successful commit. |
| 216 | Returns `0`. | Signals success. |

## `_run_find`: lines 219–266

```python
219  def _run_find(args: argparse.Namespace) -> int:
220      _reject_output_input_collisions(
221          [args.output, args.members_output, args.report],
222          [args.alignment, args.tree, args.clade_tips, args.outgroup_file],
223      )
224      alignment = read_transposed_nexus(args.alignment)
225      tree, rooting = _root_tree(read_newick(args.tree), args)
226      validate_compatibility(alignment, tree)
227      branch, selector = _select_branch(tree, args)
228      summary = analyse_branch(
229          alignment=alignment,
230          tree=tree,
231          branch=branch,
232          mode=args.mode,
233          include_ambiguous=args.include_ambiguous,
234      )
235  
236      targets = [args.output, args.members_output, args.report]
237      with AtomicOutputSet(targets, force=args.force) as transaction:
238          staged_results = transaction.staged_path(args.output)
239          staged_members = transaction.staged_path(args.members_output)
240          staged_report = transaction.staged_path(args.report)
241          write_results(staged_results, summary.results)
242          write_members(staged_members, branch)
243          report = build_report(
244              alignment=alignment,
245              alignment_path=args.alignment,
246              tree=tree,
247              tree_path=args.tree,
248              branch=branch,
249              rooting=rooting,
250              selector=selector,
251              mode=args.mode,
252              include_ambiguous=args.include_ambiguous,
253              summary=summary,
254              results_path=args.output,
255              members_path=args.members_output,
256              results_hash_path=staged_results,
257              members_hash_path=staged_members,
258          )
259          write_report(staged_report, report)
260          transaction.commit()
261  
262      print(
263          f"Selected {branch.short_id} ({branch.descendant_count} descendants); "
264          f"reported {summary.reported_sites} of {summary.sites_examined} sites."
265      )
266      return 0
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 219 | Defines the main analytical handler. | Coordinates all major modules. |
| 220–223 | Rejects any output that aliases alignment, tree, clade-tip file, or outgroup file. | Output/output collisions are checked later by `AtomicOutputSet`. |
| 224 | Parses the alignment. | Stops before any outputs are staged if malformed. |
| 225 | Parses and roots the tree. | Rooting precedes branch selection and change direction. |
| 226 | Validates exact taxon compatibility. | Returned count object is unnecessary here, so it is discarded. |
| 227 | Selects one focal branch and selector metadata. | The branch contains exact sorted descendants and a deterministic ID. |
| 228–234 | Analyses every site using the selected mode and ambiguity flag. | Returns rows plus complete counts for all parsimony statuses. |
| 236 | Orders the three final target paths. | This order is also the replacement order at commit. |
| 237 | Opens one staging context for all outputs. | All writers complete before commit is called. |
| 238–240 | Retrieves the three temporary paths. | These are real files created in each target directory. |
| 241 | Writes the results TSV to staging. | File hash can be computed before final placement. |
| 242 | Writes sorted branch members to staging. | Membership content is tied to the selected `BranchRecord`. |
| 243–258 | Builds the report from inputs, rooted branch metadata, parameters, counts, final basenames, and hashes of staged results/members. | The report names intended outputs while hashing completed bytes before they are committed. |
| 259 | Writes deterministic JSON to staging. | The report does not hash itself. |
| 260 | Commits the staged files. | Replacements occur sequentially; see chapter 10 for the exact atomicity boundary. |
| 262–265 | Prints branch short ID, descendant count, and reported/examined site counts. | Occurs after commit. |
| 266 | Returns `0`. | Signals success. |

## `main`: lines 269–286

```python
269  def main(argv: list[str] | None = None) -> int:
270      parser = build_parser()
271      args = parser.parse_args(argv)
272      try:
273          if args.command == "validate":
274              return _run_validate(args)
275          if args.command == "inspect":
276              return _run_inspect(args)
277          if args.command == "find":
278              return _run_find(args)
279          parser.error("Unknown command.")
280      except BranchSNVError as exc:
281          print(f"BRANCHSNV error: {exc}", file=sys.stderr)
282          return 2
283      except OSError as exc:
284          print(f"BRANCHSNV I/O error: {exc}", file=sys.stderr)
285          return 2
286      return 1
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 269 | Defines the public dispatcher. `argv=None` means use process arguments. | Tests can pass a list directly without spawning a subprocess. |
| 270 | Builds the parser. | Parser state is not global. |
| 271 | Parses arguments. | Missing/invalid options cause `argparse` to raise `SystemExit(2)` before the following `try`. |
| 272 | Starts expected runtime-error handling. | Covers parsing files, rooting, selection, analysis, and writing. |
| 273–278 | Dispatches the three known command names and returns handler status. | Each successful handler currently returns `0`. |
| 279 | Calls `parser.error` for an unknown command. | Defensive; required registered subparsers make it unreachable through normal parsing. |
| 280–282 | Catches any `BranchSNVError`, prints a concise stderr message, returns `2`. | Format, compatibility, and selection failures share one user-facing policy. |
| 283–285 | Catches remaining `OSError`, labels it as I/O, returns `2`. | Covers unwrapped filesystem failures. |
| 286 | Returns `1` as a final fallback. | Effectively unreachable in current control flow; unexpected non-caught exceptions propagate instead. |

## CLI invariants

1. Rooting is always explicit at the parser level.
2. Branch selection is always explicit for `find`.
3. Outputs cannot intentionally replace inputs.
4. Expected user errors do not produce tracebacks.
5. `find` stages all outputs only after parsing, rooting, compatibility, selection, and analysis have succeeded.

## Tests most relevant to this chapter

- `test_cli.py`: command success, deterministic output objects, LF endings, overwrite refusal, input protection.
- `test_process_determinism.py`: cross-process byte stability under different hash seeds.
- `test_release_metadata.py`: version agreement.
