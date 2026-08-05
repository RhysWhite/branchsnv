# 04 — Newick parser

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `src/branchsnv/newick.py (lines 1–186)`  
**Last checked against source:** 5 August 2026

This chapter covers conversion of Newick text into parent-linked `Node` objects. Rooting and branch operations are covered in chapter 05.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Module header and parser state: lines 1–18

```python
 1  """Dependency-free Newick parsing and deterministic rooted-tree operations."""
 2  
 3  from __future__ import annotations
 4  
 5  import math
 6  from dataclasses import dataclass
 7  from pathlib import Path
 8  
 9  from .errors import NewickFormatError, SelectionError, ValidationError
10  from .models import BranchRecord, Node, Tree
11  from .util import sha256_lines
12  
13  
14  @dataclass
15  class _Parser:
16      text: str
17      index: int = 0
18  
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1 | Module docstring. | Parser and tree operations have no third-party dependency. |
| 3–11 | Imports annotations, finite-number checking, dataclass, path handling, exceptions/models, and line hashing. | `sha256_lines` is used later for branch IDs. |
| 14 | Makes `_Parser` a mutable dataclass. | The cursor advances through one text string. |
| 15–17 | Stores complete Newick text and current zero-based character index. | One parser instance handles one tree. |

## `_Parser.parse`: lines 19–31

```python
19      def parse(self) -> Tree:
20          self._skip_space_and_comments()
21          root = self._parse_subtree()
22          self._skip_space_and_comments()
23          if self._peek() != ";":
24              raise self._error("Expected ';' at the end of the Newick tree")
25          self.index += 1
26          self._skip_space_and_comments()
27          if self.index != len(self.text):
28              raise self._error("Unexpected content after the terminating ';'")
29          root.parent = None
30          self._validate(root)
31          return Tree(root=root)
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 19 | Defines the top-level parser method. | Returns a `Tree`, not a bare root. |
| 20 | Skips leading whitespace/comments. | Rooted annotations such as `[&R]` are ignored as comments. |
| 21 | Recursively parses one subtree, which is the whole tree. | Recursion follows Newick nesting depth. |
| 22 | Skips whitespace/comments after the root representation. | Allows comments before the semicolon. |
| 23–24 | Requires a terminating semicolon. | Multiple unterminated/concatenated trees are not accepted. |
| 25 | Consumes the semicolon. | Moves cursor past the tree. |
| 26 | Skips trailing whitespace/comments. | Harmless trailing comments are accepted. |
| 27–28 | Rejects any other content after the semicolon. | Exactly one tree per input text. |
| 29 | Explicitly removes any parent pointer from the root. | Establishes rooted-tree invariant. |
| 30 | Validates structural and label invariants. | Checks internal degree and duplicate tip names. |
| 31 | Wraps root in `Tree`. | Public traversal methods then become available. |

## `_parse_subtree`: lines 33–55

```python
33      def _parse_subtree(self) -> Node:
34          self._skip_space_and_comments()
35          if self._peek() == "(":
36              self.index += 1
37              children = [self._parse_subtree()]
38              self._skip_space_and_comments()
39              while self._peek() == ",":
40                  self.index += 1
41                  children.append(self._parse_subtree())
42                  self._skip_space_and_comments()
43              if self._peek() != ")":
44                  raise self._error("Expected ')' to close an internal node")
45              self.index += 1
46              name = self._parse_optional_label()
47              length = self._parse_optional_length()
48              node = Node(name=name, length=length, children=children)
49              for child in children:
50                  child.parent = node
51              return node
52  
53          name = self._parse_required_label()
54          length = self._parse_optional_length()
55          return Node(name=name, length=length)
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 33–34 | Defines recursive subtree parsing and skips ignorable material. | Every call begins at a tip or `(`. |
| 35–36 | Detects and consumes `(` for an internal node. | Enters child-list mode. |
| 37 | Parses the first child immediately. | Empty internal child lists fail through required-label parsing rather than being accepted. |
| 38–42 | Repeatedly consumes commas and parses more children. | Polytomies are supported. |
| 43–45 | Requires and consumes matching `)`. | Malformed nesting gets a line/column error. |
| 46 | Parses optional internal label. | Labels are display metadata. |
| 47 | Parses optional incoming branch length. | A root length may parse but is not used analytically. |
| 48 | Creates internal node with child list. | Parent remains unset until next lines. |
| 49–50 | Sets each child's parent pointer to the new node. | Produces bidirectional navigation. |
| 51 | Returns the internal node. | Its parent is assigned by its caller. |
| 53 | For a non-`(` start, requires a tip label. | Unlabelled tips are invalid. |
| 54 | Parses optional tip branch length. | Stored as the tip node's incoming edge length. |
| 55 | Returns a leaf `Node`. | Empty child list makes `is_tip=True`. |

## Label parsing: lines 57–92

```python
57      def _parse_required_label(self) -> str:
58          label = self._parse_optional_label()
59          if label is None or label == "":
60              raise self._error("Tip labels must not be empty")
61          return label
62  
63      def _parse_optional_label(self) -> str | None:
64          self._skip_space_and_comments()
65          char = self._peek()
66          if char in {None, ":", ",", ")", ";"}:
67              return None
68          if char == "'":
69              self.index += 1
70              chars: list[str] = []
71              while self.index < len(self.text):
72                  current = self.text[self.index]
73                  if current == "'":
74                      if self.index + 1 < len(self.text) and self.text[self.index + 1] == "'":
75                          chars.append("'")
76                          self.index += 2
77                          continue
78                      self.index += 1
79                      return "".join(chars)
80                  chars.append(current)
81                  self.index += 1
82              raise self._error("Unterminated quoted Newick label")
83  
84          start = self.index
85          while self.index < len(self.text):
86              current = self.text[self.index]
87              if current.isspace() or current in {":", ",", "(", ")", ";", "["}:
88                  break
89              self.index += 1
90          if self.index == start:
91              return None
92          return self.text[start:self.index]
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 57–61 | `_parse_required_label` delegates to optional parsing, then rejects `None` or empty text. | Used only for tips. |
| 63–67 | `_parse_optional_label` skips ignorable text and returns `None` before delimiters/end. | Internal labels are optional. |
| 68–82 | Parses a single-quoted label; two consecutive single quotes become one literal quote; rejects an unclosed quote. | Spaces and Newick punctuation are allowed inside single quotes. |
| 84 | Stores start cursor for unquoted label. | Enables detection of no consumed characters. |
| 85–89 | Consumes until whitespace or a Newick delimiter/comment opener. | Unquoted labels cannot contain those characters. |
| 90–91 | Returns `None` when nothing was consumed. | Supports absent internal labels. |
| 92 | Returns the raw unquoted substring. | Underscores are not transformed into spaces. |

Only single quotes receive Newick quote semantics in this parser. A double quote is not treated as a quote delimiter by `_parse_optional_label`; this is part of the supported-subset boundary.

## Branch-length parsing: lines 94–115

```python
 94      def _parse_optional_length(self) -> float | None:
 95          self._skip_space_and_comments()
 96          if self._peek() != ":":
 97              return None
 98          self.index += 1
 99          self._skip_space_and_comments()
100          start = self.index
101          while self.index < len(self.text):
102              char = self.text[self.index]
103              if char.isspace() or char in {",", ")", ";", "["}:
104                  break
105              self.index += 1
106          token = self.text[start:self.index]
107          if not token:
108              raise self._error("Branch length is missing after ':'")
109          try:
110              value = float(token)
111          except ValueError as exc:
112              raise self._error(f"Invalid branch length: {token!r}") from exc
113          if not math.isfinite(value):
114              raise self._error("Branch lengths must be finite")
115          return value
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 94–97 | Skips ignorable text and returns `None` unless the next character is `:`. | Lengths are optional. |
| 98–100 | Consumes colon, skips whitespace/comments, records token start. | Comments can appear between colon and number. |
| 101–105 | Consumes token until whitespace, structural delimiter, semicolon, or comment. | Scientific notation and signs are accepted if `float()` accepts them. |
| 106–108 | Rejects missing text after colon. | Avoids a generic `float('')` error. |
| 109–112 | Converts to float; wraps invalid text as `NewickFormatError`. | Error includes source location through `_error`. |
| 113–114 | Rejects NaN and positive/negative infinity. | Lengths must be finite, though negative finite lengths are not explicitly prohibited. |
| 115 | Returns the float. | Values are preserved through rerooting where possible. |

## Whitespace/comments, lookahead, and diagnostics: lines 117–144

```python
117      def _skip_space_and_comments(self) -> None:
118          while self.index < len(self.text):
119              if self.text[self.index].isspace():
120                  self.index += 1
121                  continue
122              if self.text[self.index] == "[":
123                  depth = 1
124                  self.index += 1
125                  while self.index < len(self.text) and depth:
126                      if self.text[self.index] == "[":
127                          depth += 1
128                      elif self.text[self.index] == "]":
129                          depth -= 1
130                      self.index += 1
131                  if depth:
132                      raise self._error("Unterminated Newick comment")
133                  continue
134              break
135  
136      def _peek(self) -> str | None:
137          if self.index >= len(self.text):
138              return None
139          return self.text[self.index]
140  
141      def _error(self, message: str) -> NewickFormatError:
142          line = self.text.count("\n", 0, self.index) + 1
143          column = self.index - self.text.rfind("\n", 0, self.index)
144          return NewickFormatError(f"{message} at line {line}, column {column}.")
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 117–121 | Repeatedly consumes whitespace. | Newlines and indentation are accepted. |
| 122–133 | Parses nested square-bracket comments by depth; rejects an unclosed comment. | Comment contents are discarded. |
| 134 | Stops on first syntactically meaningful character. | Caller then decides what token is expected. |
| 136–139 | `_peek` returns current character or `None` at end. | Avoids repeated bounds checks in parser methods. |
| 141–144 | `_error` computes one-based line and column and returns `NewickFormatError`. | The caller raises the returned exception, preserving a consistent suffix and punctuation. |

## Structural validation: lines 146–167

```python
146      @staticmethod
147      def _validate(root: Node) -> None:
148          stack = [root]
149          tip_names: list[str] = []
150          while stack:
151              node = stack.pop()
152              if node.is_tip:
153                  if node.name is None:
154                      raise NewickFormatError("Every tip must have a label.")
155                  tip_names.append(node.name)
156              elif len(node.children) < 2:
157                  raise NewickFormatError("Internal Newick nodes must have at least two children.")
158              stack.extend(node.children)
159          seen: set[str] = set()
160          duplicates: set[str] = set()
161          for name in tip_names:
162              if name in seen:
163                  duplicates.add(name)
164              seen.add(name)
165          if duplicates:
166              preview = ", ".join(sorted(duplicates)[:5])
167              raise NewickFormatError(f"Duplicate tree tip label(s): {preview}.")
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 146–147 | Defines static validation independent of parser instance state. | Reused after rerooting in chapter 05. |
| 148–150 | Iteratively traverses from root and collects tip names. | Avoids recursion for validation. |
| 151–158 | Requires every tip to have a name and every internal node to have at least two children; pushes children. | Unary internal nodes are forbidden. |
| 159–164 | Tracks seen names and a duplicate set. | Nodes remain identity-distinct even when labels repeat, so explicit label checking is required. |
| 165–167 | Raises with a sorted preview of up to five duplicate tip names. | Tree/alignment matching would otherwise be ambiguous. |

## Public text/file readers: lines 171–186

```python
171  def parse_newick(text: str) -> Tree:
172      """Parse one Newick tree from text."""
173  
174      if not text.strip():
175          raise NewickFormatError("Newick text is empty.")
176      return _Parser(text).parse()
177  
178  def read_newick(path: str | Path) -> Tree:
179      source = Path(path)
180      try:
181          text = source.read_text(encoding="utf-8-sig")
182      except OSError as exc:
183          raise NewickFormatError(f"Could not read Newick file {source}: {exc}") from exc
184      if not text.strip():
185          raise NewickFormatError("Newick file is empty.")
186      return parse_newick(text)
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 171–176 | `parse_newick` rejects all-whitespace text, then instantiates `_Parser` and parses. | Useful for tests and programmatic use. |
| 178–179 | `read_newick` converts string/path to `Path`. | Public file reader. |
| 180–183 | Reads UTF-8 with optional BOM; wraps `OSError` as `NewickFormatError`. | As with NEXUS, decoding errors are not `OSError` in this version. |
| 184–185 | Rejects an empty/whitespace file before calling parser. | Gives a file-specific message. |
| 186 | Delegates to `parse_newick`. | All syntax and structural checks stay centralised. |

## Tests most relevant to this chapter

- labels, branch lengths, comments, and polytomy;
- duplicate tip rejection;
- existing-root and reroot tests indirectly revalidate parsed structure.
