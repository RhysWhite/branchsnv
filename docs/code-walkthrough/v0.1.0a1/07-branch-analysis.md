# 07 — Branch-associated site analysis

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `src/branchsnv/analysis.py`  
**Last checked against source:** 5 August 2026

This chapter explains how strict fixed-exclusive markers and focal-edge parsimony reconstruction are evaluated for every alignment row and combined according to reporting mode.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Imports and summary record: lines 1–22

```python
 1  """Branch-associated SNV analysis."""
 2  
 3  from __future__ import annotations
 4  
 5  from collections import Counter
 6  from dataclasses import dataclass
 7  
 8  from .models import Alignment, BranchRecord, SiteResult, Tree
 9  from .parsimony import compile_tree, reconstruct_site
10  from .util import parse_coordinate
11  
12  
13  @dataclass(frozen=True)
14  class AnalysisSummary:
15      results: tuple[SiteResult, ...]
16      sites_examined: int
17      fixed_exclusive_sites: int
18      unambiguous_change_sites: int
19      change_state_ambiguous_sites: int
20      placement_ambiguous_sites: int
21      no_change_sites: int
22      reported_sites: int
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1–10 | Docstring, imports, models, parsimony functions, coordinate parser. | `Counter` accumulates all site statuses. |
| 13–22 | Defines immutable `AnalysisSummary`. | Stores reported rows plus total counts for every site, including statuses not selected for output. |

## `_is_unambiguous_base`: lines 25–26

```python
25  def _is_unambiguous_base(symbol: str) -> bool:
26      return symbol.upper() in {"A", "C", "G", "T"}
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 25 | Defines a private predicate. | Used only by the fixed-exclusive definition. |
| 26 | Returns true only for A/C/G/T after uppercasing. | IUPAC ambiguity symbols, `N`, gaps, and missing are non-callable for strict marker analysis. |

## `analyse_branch`: lines 29–151

```python
 29  def analyse_branch(
 30      alignment: Alignment,
 31      tree: Tree,
 32      branch: BranchRecord,
 33      mode: str,
 34      include_ambiguous: bool = False,
 35  ) -> AnalysisSummary:
 36      if mode not in {"fixed-exclusive", "parsimony", "both"}:
 37          raise ValueError(f"Unknown analysis mode: {mode}")
 38  
 39      taxon_index = alignment.taxon_index
 40      descendant_indices = tuple(taxon_index[name] for name in branch.descendant_tips)
 41      descendant_set = set(descendant_indices)
 42      outside_indices = tuple(index for index in range(alignment.ntax) if index not in descendant_set)
 43      compiled = compile_tree(tree, branch.node, taxon_index)
 44  
 45      results: list[SiteResult] = []
 46      fixed_exclusive_count = 0
 47      status_counts = Counter()
 48  
 49      for site in alignment.sites:
 50          descendant_symbols = [site.states[index].upper() for index in descendant_indices]
 51          outside_symbols = [site.states[index].upper() for index in outside_indices]
 52  
 53          descendant_callable = sum(_is_unambiguous_base(symbol) for symbol in descendant_symbols)
 54          outside_callable = sum(_is_unambiguous_base(symbol) for symbol in outside_symbols)
 55          callable_descendant_states = [
 56              symbol for symbol in descendant_symbols if _is_unambiguous_base(symbol)
 57          ]
 58          descendant_state = ""
 59          fixed_within = False
 60          descendant_state_count = 0
 61          if descendant_callable == len(descendant_indices) and callable_descendant_states:
 62              unique = set(callable_descendant_states)
 63              if len(unique) == 1:
 64                  descendant_state = callable_descendant_states[0]
 65                  fixed_within = True
 66                  descendant_state_count = descendant_callable
 67  
 68          outside_same_count = (
 69              sum(symbol == descendant_state for symbol in outside_symbols)
 70              if descendant_state
 71              else 0
 72          )
 73          exclusive = (
 74              fixed_within
 75              and outside_callable == len(outside_indices)
 76              and outside_same_count == 0
 77          )
 78          fixed_exclusive = fixed_within and exclusive
 79          if fixed_exclusive:
 80              fixed_exclusive_count += 1
 81  
 82          parsimony = reconstruct_site(
 83              compiled=compiled,
 84              states=site.states,
 85              gap=alignment.gap,
 86              missing=alignment.missing,
 87          )
 88          status_counts[parsimony.status] += 1
 89  
 90          selected_fixed = mode in {"fixed-exclusive", "both"} and fixed_exclusive
 91          selected_parsimony = mode in {"parsimony", "both"} and (
 92              parsimony.status == "unambiguous_change"
 93              or (include_ambiguous and parsimony.status in {"change_state_ambiguous", "placement_ambiguous"})
 94          )
 95          if not (selected_fixed or selected_parsimony):
 96              continue
 97  
 98          if selected_fixed and selected_parsimony:
 99              reason = "both"
100          elif selected_fixed:
101              reason = "fixed-exclusive"
102          else:
103              reason = "parsimony"
104  
105          if len(parsimony.possible_pairs) == 1:
106              parent_state, child_state = parsimony.possible_pairs[0]
107              change = f"{parent_state}>{child_state}" if parent_state != child_state else ""
108          else:
109              change = "|".join(
110                  f"{parent}>{child}" for parent, child in parsimony.possible_pairs if parent != child
111              )
112  
113          reference, position = parse_coordinate(site.site_id)
114          results.append(
115              SiteResult(
116                  site_id=site.site_id,
117                  reference=reference,
118                  position=position,
119                  input_row=site.input_row,
120                  parent_states="|".join(parsimony.parent_states),
121                  child_states="|".join(parsimony.child_states),
122                  possible_pairs="|".join(
123                      f"{parent}>{child}" for parent, child in parsimony.possible_pairs
124                  ),
125                  change=change,
126                  parsimony_status=parsimony.status,
127                  fixed_within_clade=fixed_within,
128                  exclusive_to_clade=exclusive,
129                  descendant_state=descendant_state,
130                  descendant_total=len(descendant_indices),
131                  descendant_callable=descendant_callable,
132                  descendant_state_count=descendant_state_count,
133                  outside_total=len(outside_indices),
134                  outside_callable=outside_callable,
135                  outside_same_state_count=outside_same_count,
136                  parsimony_score=parsimony.score,
137                  selection_reason=reason,
138              )
139          )
140  
141      results.sort(key=lambda item: item.input_row)
142      return AnalysisSummary(
143          results=tuple(results),
144          sites_examined=alignment.nchar,
145          fixed_exclusive_sites=fixed_exclusive_count,
146          unambiguous_change_sites=status_counts["unambiguous_change"],
147          change_state_ambiguous_sites=status_counts["change_state_ambiguous"],
148          placement_ambiguous_sites=status_counts["placement_ambiguous"],
149          no_change_sites=status_counts["no_change"],
150          reported_sites=len(results),
151      )
```

### Preconditions and reusable indexing: lines 29–47

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 29–35 | Defines analysis inputs and optional ambiguity reporting. | Returns one immutable summary. |
| 36–37 | Rejects an unknown programmatic mode with `ValueError`. | CLI choices prevent this through normal use; it is not wrapped as `BranchSNVError`. |
| 39 | Builds exact alignment taxon index. | New dictionary from `Alignment.taxon_index`. |
| 40 | Converts sorted branch descendant names into alignment column indices. | Exact name mapping, not tree order. |
| 41 | Builds set for fast outside-index exclusion. | Membership lookup avoids repeated tuple scanning. |
| 42 | Creates tuple of every alignment index not in descendant set. | Defines the comparison side. |
| 43 | Compiles rooted tree and focal edge once. | Avoids recompiling topology for every site. |
| 45–47 | Initialises reported results, fixed-exclusive count, and parsimony status counter. | Counts include unreported rows. |

### Strict fixed-exclusive calculation: lines 49–80

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 49 | Iterates alignment sites in original order. | Every site is examined exactly once. |
| 50–51 | Extracts uppercase states for descendants and outside taxa. | Index tuples preserve alignment mapping. |
| 53–54 | Counts canonical A/C/G/T calls on each side. | Python sums Boolean values as 1/0. |
| 55–57 | Builds list of callable descendant bases. | Reuses predicate; ambiguous states are excluded. |
| 58–60 | Initialises empty descendant state, false fixed flag, and zero supporting count. | Defaults describe a non-fixed or non-callable descendant set. |
| 61 | Proceeds only when all descendants are callable and list is nonempty. | Full call rate is mandatory. |
| 62 | Builds set of descendant bases. | Tests fixation. |
| 63–66 | If exactly one base exists, records it, marks fixed, and sets supporting count equal to number of callable descendants. | With full callability, state count equals total descendants. |
| 68–72 | Counts outside symbols exactly equal to descendant state, or zero when no state was established. | Count is only meaningful for a fixed descendant base. |
| 73–77 | Defines `exclusive` as fixed descendants + all outside taxa callable + zero outside matches. | The explicit outside full-call requirement prevents missing data from masquerading as exclusivity. |
| 78 | Defines `fixed_exclusive` as `fixed_within and exclusive`. | `exclusive` already includes `fixed_within`, so this conjunction is logically redundant but harmless. |
| 79–80 | Increments total strict marker count. | Count is independent of reporting mode. |

### Parsimony reconstruction and reporting selection: lines 82–103

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 82–87 | Reconstructs the site with compiled tree, raw state string, and configured gap/missing. | Parsimony runs even in `fixed-exclusive` mode so rows/counts still contain reconstruction information. |
| 88 | Increments count for returned status. | `Counter` defaults missing keys to zero. |
| 90 | Selects strict marker route when mode includes it and site qualifies. | `both` includes this route. |
| 91–94 | Selects parsimony route for `unambiguous_change`, or for two ambiguous statuses only when `include_ambiguous=True`. | `no_change` is never reported solely because of parsimony. |
| 95–96 | Skips row unless either route selected it. | Counts remain complete because they were updated first. |
| 98–103 | Assigns selection reason `both`, `fixed-exclusive`, or `parsimony`. | Explains why each TSV row exists. |

### Change text and result construction: lines 105–139

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 105–107 | For exactly one optimal pair, unpacks it and writes `P>C` only if states differ; otherwise blank. | A unique no-change pair has empty `change`. |
| 108–111 | For multiple pairs, joins only changing pairs with `|`. | In placement-ambiguous cases, the `change` column summarises possible changes while `possible_pairs` retains both change and no-change pairs. |
| 113 | Splits terminal `_integer` coordinate from site ID when possible. | Original `site_id` is always retained. |
| 114–139 | Builds `SiteResult` with coordinate fields, joined sorted state/pair strings, strict marker flags/counts, global score, and selection reason. | Field order corresponds to writer contract, although keyword construction does not depend on order. |

### Deterministic return: lines 141–151

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 141 | Sorts selected rows by original logical matrix row. | Protects output order even if future selection construction changes. |
| 142–151 | Returns immutable summary with tuple results, declared site count, strict marker count, each status count, and reported row count. | Sum of the four parsimony status counts should equal `sites_examined`; provenance tests assert this. |

## Important distinctions in output fields

- `parent_states`/`child_states`: distinct states occurring in any optimal pair.
- `possible_pairs`: complete pair set, including no-change pairs.
- `change`: convenient display of only changing pairs; not the full ambiguity record.
- `fixed_within_clade`: all descendants callable and identical.
- `exclusive_to_clade`: in this implementation also requires `fixed_within_clade` and complete outside callability.
- `selection_reason`: which mode rule caused reporting, not the biological interpretation by itself.

## Tests most relevant to this chapter

- default `both` mode reports the union;
- missing descendants prevent strict fixed calls;
- missing outside taxa prevent exclusivity;
- ambiguous parsimony rows appear only with the option;
- expected simple-example rows and counts are exercised through CLI/provenance tests.
