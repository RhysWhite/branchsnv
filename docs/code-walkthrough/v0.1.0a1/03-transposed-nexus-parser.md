# 03 — Transposed NEXUS parser

**BRANCHSNV version:** `0.1.0a1`  
**Source archive commit:** [`582d3883d39adb8c591d9eb152143227c9696eec`](https://github.com/RhysWhite/branchsnv/tree/582d3883d39adb8c591d9eb152143227c9696eec)  
**Source file(s):** `src/branchsnv/nexus.py`  
**Last checked against source:** 5 August 2026

This chapter explains the strict dependency-free parser that turns one supported transposed nucleotide NEXUS block into an immutable `Alignment`.

> This document describes the source at the commit above. It is not a substitute
> for the executable code or tests. A table row may cover several continuation
> lines belonging to one Python statement, but every non-blank production source
> line is included in the coverage ledger.

## Module constants and imports: lines 1–12

```python
 1  """Strict parser for the transposed nucleotide NEXUS subset used by BRANCHSNV."""
 2  
 3  from __future__ import annotations
 4  
 5  import re
 6  from collections import Counter
 7  from pathlib import Path
 8  
 9  from .errors import NexusFormatError
10  from .models import Alignment, Site
11  
12  _IUPAC = frozenset("ACGTRYSWKMBDHVN")
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 1 | States that this is a strict parser for BRANCHSNV's supported subset. | It is not a general NEXUS implementation. |
| 3–10 | Imports annotations, regex, `Counter`, `Path`, format error, and models. | `Counter` detects duplicate taxon labels. |
| 12 | Defines accepted IUPAC nucleotide symbols. | Includes canonical bases, ambiguity codes, and `N`; gap and missing are added dynamically. |

## `_strip_comments`: lines 15–55

```python
15  def _strip_comments(text: str) -> str:
16      """Remove nested NEXUS comments while preserving line breaks and quoted text."""
17  
18      output: list[str] = []
19      depth = 0
20      quote: str | None = None
21      index = 0
22      while index < len(text):
23          char = text[index]
24          if quote is not None:
25              output.append(char if depth == 0 else ("\n" if char == "\n" else " "))
26              if char == quote:
27                  # NEXUS single-quoted strings escape a quote by doubling it.
28                  if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
29                      index += 1
30                      output.append(text[index] if depth == 0 else " ")
31                  else:
32                      quote = None
33              index += 1
34              continue
35  
36          if depth == 0 and char in {"'", '"'}:
37              quote = char
38              output.append(char)
39          elif char == "[":
40              depth += 1
41              output.append(" ")
42          elif char == "]" and depth:
43              depth -= 1
44              output.append(" ")
45          elif depth:
46              output.append("\n" if char == "\n" else " ")
47          else:
48              output.append(char)
49          index += 1
50  
51      if depth:
52          raise NexusFormatError("Unterminated NEXUS comment.")
53      if quote is not None:
54          raise NexusFormatError("Unterminated quoted string in NEXUS file.")
55      return "".join(output)
```

**Purpose:** remove nested square-bracket comments while preserving newlines and quoted content, so later line numbers remain useful.

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 15–16 | Defines the helper and its contract. | It returns text of the same general line structure, with comments blanked. |
| 18–21 | Initialises output characters, comment nesting depth, active quote, and cursor. | `depth=0` means normal text. |
| 22–23 | Iterates character by character. | Necessary because regex alone does not safely handle nested comments and quotes. |
| 24–34 | When inside a quoted string, copies characters; recognises doubled single quotes; closes only on an unescaped matching quote. | Brackets inside quoted labels are preserved rather than treated as comments. |
| 25 | If a quote somehow exists while comment depth is nonzero, replaces comment content with spaces/newlines. | Normal control flow only opens quotes at depth zero. |
| 36–38 | Opens single- or double-quoted text only outside comments and preserves the quote. | Later tokenisation can recover the token. |
| 39–41 | On `[`, increments nesting depth and emits a space. | Nested comments are supported. |
| 42–44 | On `]` while in a comment, decrements depth and emits a space. | A `]` outside a comment is left as ordinary text. |
| 45–46 | Replaces every non-newline comment character with a space. | Keeps approximate character positions and exact line count. |
| 47–48 | Copies ordinary text unchanged. | Parser-relevant content survives. |
| 49 | Advances cursor. | Every loop consumes at least one character. |
| 51–52 | Rejects an unclosed comment. | Produces `NexusFormatError`. |
| 53–54 | Rejects an unclosed quoted string. | Prevents later parsers from receiving ambiguous content. |
| 55 | Joins the output character list. | Returns the comment-stripped text. |

## `_split_commands`: lines 58–91

```python
58  def _split_commands(text: str) -> list[tuple[str, int]]:
59      """Split a NEXUS block into semicolon-terminated commands."""
60  
61      commands: list[tuple[str, int]] = []
62      start = 0
63      line = 1
64      start_line = 1
65      quote: str | None = None
66      index = 0
67      while index < len(text):
68          char = text[index]
69          if quote is not None:
70              if char == quote:
71                  if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
72                      index += 1
73                  else:
74                      quote = None
75          elif char in {"'", '"'}:
76              quote = char
77          elif char == ";":
78              command = text[start:index].strip()
79              if command:
80                  commands.append((command, start_line))
81              start = index + 1
82              start_line = line
83          if char == "\n":
84              line += 1
85              if start == index + 1:
86                  start_line = line
87          index += 1
88  
89      if text[start:].strip():
90          raise NexusFormatError("NEXUS command is not terminated by a semicolon.")
91      return commands
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 58–59 | Defines semicolon command splitting. | Each return item is `(command_text_without_semicolon, starting_line)`. |
| 61–66 | Initialises output, text slice start, current line, command start line, quote, and cursor. | Line tracking supports matrix diagnostics. |
| 67–76 | Scans text while tracking quoted text and doubled single quotes. | Semicolons inside quoted labels do not end commands. |
| 77–82 | At an unquoted semicolon, strips and records a nonempty command, then starts the next slice. | Empty commands are ignored. |
| 83–86 | Increments the running line number on each newline. The nested `start == index + 1` condition is not reached by the current cursor update sequence, so it does not advance `start_line`. | Command start lines therefore remain approximate and can refer to the line containing the preceding semicolon rather than the first content line. See chapter 10. |
| 87 | Advances cursor. | Completes the scan. |
| 89–90 | Rejects any trailing non-whitespace text not terminated by `;`. | Every supported command must be semicolon-terminated. |
| 91 | Returns commands. | Unknown commands may later be ignored. |

## `_unquote` and `_tokenize`: lines 94–135

```python
 94  def _unquote(token: str) -> str:
 95      token = token.strip()
 96      if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
 97          inner = token[1:-1]
 98          if token[0] == "'":
 99              return inner.replace("''", "'")
100          return inner
101      return token
102  
103  
104  def _tokenize(text: str) -> list[str]:
105      tokens: list[str] = []
106      current: list[str] = []
107      quote: str | None = None
108      index = 0
109      while index < len(text):
110          char = text[index]
111          if quote is not None:
112              current.append(char)
113              if char == quote:
114                  if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
115                      index += 1
116                      current.append(text[index])
117                  else:
118                      quote = None
119              index += 1
120              continue
121          if char in {"'", '"'}:
122              quote = char
123              current.append(char)
124          elif char.isspace():
125              if current:
126                  tokens.append(_unquote("".join(current)))
127                  current = []
128          else:
129              current.append(char)
130          index += 1
131      if quote is not None:
132          raise NexusFormatError("Unterminated quoted token.")
133      if current:
134          tokens.append(_unquote("".join(current)))
135      return tokens
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 94–101 | Strips a token; if it has matching outer single/double quotes, removes them; undoubles single quotes. | Double-quoted content is returned literally inside the quotes; no special doubled-double-quote rule is implemented. |
| 104–109 | Starts whitespace tokenisation with quote awareness. | Used for `TAXLABELS` and each matrix row. |
| 110–120 | While quoted, appends every character; handles doubled single quotes; exits on matching quote. | Whitespace inside a quoted taxon/site label stays inside one token. |
| 121–123 | Opens a quoted token. | Quote characters are retained until `_unquote`. |
| 124–128 | On whitespace, emits the current token if nonempty. | Consecutive whitespace is harmless. |
| 129–130 | Appends ordinary characters. | Punctuation is not independently tokenised. |
| 131 | Advances cursor. | Continues scan. |
| 131–132 | Rejects an unclosed quote. | Defensive even though `_strip_comments` also checks the full file. |
| 133–135 | Emits the final token if present, then returns the list. | Tokens are unquoted before return. |

## `_find_data_block`: lines 138–150

```python
138  def _find_data_block(text: str) -> str:
139      pattern = re.compile(r"\bbegin\s+(data|characters)\s*;", re.IGNORECASE)
140      matches = list(pattern.finditer(text))
141      if not matches:
142          raise NexusFormatError("No BEGIN DATA or BEGIN CHARACTERS block was found.")
143      if len(matches) > 1:
144          raise NexusFormatError("Multiple DATA/CHARACTERS blocks are not supported.")
145      match = matches[0]
146      remainder = text[match.end() :]
147      end_match = re.search(r"\bend(?:block)?\s*;", remainder, re.IGNORECASE)
148      if not end_match:
149          raise NexusFormatError("The DATA block has no terminating END; statement.")
150      return remainder[: end_match.start()]
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 138 | Defines extraction of one DATA or CHARACTERS block. | Returns only text inside that block. |
| 139–140 | Compiles case-insensitive `BEGIN DATA;`/`BEGIN CHARACTERS;` pattern and finds all matches. | Word boundaries avoid partial keyword matches. |
| 141–144 | Requires exactly one matching block start. | Multiple character blocks are intentionally unsupported. |
| 145–147 | Takes text after the block start and finds first `END;` or `ENDBLOCK;`. | Matching is case-insensitive. |
| 148–149 | Rejects a missing terminator. | Prevents accidentally consuming later blocks. |
| 150 | Returns text preceding the terminator. | The terminator itself is excluded. |

This regex-based block finder is intentionally narrow: it does not perform a full quote-aware parse of every NEXUS block in the file.

## `_parse_dimensions`: lines 153–162

```python
153  def _parse_dimensions(command: str) -> tuple[int, int]:
154      ntax_match = re.search(r"\bntax\s*=\s*(\d+)", command, re.IGNORECASE)
155      nchar_match = re.search(r"\bnchar\s*=\s*(\d+)", command, re.IGNORECASE)
156      if not ntax_match or not nchar_match:
157          raise NexusFormatError("DIMENSIONS must declare both NTAX and NCHAR.")
158      ntax = int(ntax_match.group(1))
159      nchar = int(nchar_match.group(1))
160      if ntax < 1 or nchar < 1:
161          raise NexusFormatError("NTAX and NCHAR must both be positive integers.")
162      return ntax, nchar
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 153 | Declares a return pair `(ntax, nchar)`. | Both are required. |
| 154–155 | Searches case-insensitively for non-negative digit values after `NTAX=` and `NCHAR=`. | Signs and decimal notation are not accepted. |
| 156–157 | Rejects a command missing either value. | Order does not matter. |
| 158–159 | Converts matched text to integers. | Leading zeroes are allowed but not retained. |
| 160–161 | Requires both values to be at least one. | Empty matrices are unsupported. |
| 162 | Returns dimensions. | Later checked against TAXLABELS and actual matrix rows. |

## `_parse_format`: lines 165–200

```python
165  def _parse_format(command: str) -> tuple[str, str, str]:
166      if not re.search(r"\btranspose\b", command, re.IGNORECASE):
167          raise NexusFormatError("BRANCHSNV requires FORMAT TRANSPOSE.")
168      interleave_match = re.search(
169          r"\binterleave\b(?:\s*=\s*([^\s]+))?", command, re.IGNORECASE
170      )
171      if interleave_match:
172          value = interleave_match.group(1)
173          if value is None or _unquote(value).lower() not in {"no", "false"}:
174              raise NexusFormatError("Interleaved matrices are not supported.")
175      if re.search(r"\bmatchchar\s*=", command, re.IGNORECASE):
176          raise NexusFormatError("FORMAT MATCHCHAR is not supported.")
177      if re.search(r"\bequate\s*=", command, re.IGNORECASE):
178          raise NexusFormatError("FORMAT EQUATE is not supported.")
179  
180      gap_match = re.search(r"\bgap\s*=\s*([^\s]+)", command, re.IGNORECASE)
181      missing_match = re.search(r"\bmissing\s*=\s*([^\s]+)", command, re.IGNORECASE)
182      symbols_match = re.search(
183          r"\bsymbols\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s]+))",
184          command,
185          re.IGNORECASE,
186      )
187      gap = _unquote(gap_match.group(1))[0] if gap_match else "-"
188      missing = _unquote(missing_match.group(1))[0] if missing_match else "?"
189      if symbols_match:
190          symbols = next(group for group in symbols_match.groups() if group is not None)
191      else:
192          symbols = "ACGT"
193      symbols = "".join(dict.fromkeys(symbols.upper()))
194      if not set("ACGT").issubset(set(symbols)):
195          raise NexusFormatError("FORMAT SYMBOLS must include A, C, G, and T.")
196      if len(gap) != 1 or len(missing) != 1:
197          raise NexusFormatError("GAP and MISSING symbols must each be one character.")
198      if gap == missing:
199          raise NexusFormatError("GAP and MISSING symbols must differ.")
200      return gap, missing, symbols
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 165 | Declares return `(gap, missing, symbols)`. | Values are used by matrix validation and parsimony. |
| 166–167 | Requires the word `TRANSPOSE`. | Standard taxon-as-rows matrices are rejected. |
| 168–174 | Detects `INTERLEAVE`; accepts only explicit `NO` or `FALSE`; rejects bare `INTERLEAVE` and truthy values. | The parser expects every site row in one physical matrix row. |
| 175–178 | Rejects `MATCHCHAR=` and `EQUATE=`. | Their semantics are not implemented. |
| 180–186 | Searches for GAP, MISSING, and quoted/unquoted SYMBOLS values. | Defaults are `-`, `?`, and `ACGT`. |
| 187–188 | Unquotes GAP/MISSING and takes the first character. | Current implementation therefore does not truly reject multi-character values later; see chapter 10. |
| 189–192 | Selects the captured SYMBOLS form or defaults to `ACGT`. | Quoted spaces would remain in the symbol string. |
| 193 | Uppercases symbols and removes duplicates while preserving first occurrence. | `dict.fromkeys` gives deterministic de-duplication. |
| 194–195 | Requires canonical `A`, `C`, `G`, and `T` to be present. | Ambiguity symbols need not be listed to be accepted by matrix validation. |
| 196–200 | Intends to require one-character distinct GAP and MISSING, then returns values. | Comparison occurs before final uppercasing in `Alignment`; case-only collisions are a maintenance edge case. |

## `_normalise_states`: lines 203–213

```python
203  def _normalise_states(tokens: list[str], ntax: int, row_number: int) -> str:
204      if len(tokens) == 1 and len(tokens[0]) == ntax:
205          states = tokens[0]
206      elif len(tokens) == ntax and all(len(token) == 1 for token in tokens):
207          states = "".join(tokens)
208      else:
209          raise NexusFormatError(
210              f"Matrix row {row_number} has {len(tokens)} state token(s); expected "
211              f"{ntax} single-character states or one compact string of length {ntax}."
212          )
213      return states.upper()
```

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 203 | Declares normalisation from state tokens to one uppercase string. | `row_number` is the logical matrix row, not file line. |
| 204–205 | Accepts one compact token whose length equals `NTAX`. | Example: `ACGT?`. |
| 206–207 | Or accepts exactly `NTAX` one-character tokens and joins them. | Example: `A C G T ?`. |
| 208–212 | Otherwise raises a detailed state-count error. | Rejects multicharacter per-taxon tokens and split compact fragments. |
| 213 | Uppercases all states. | Parsing and downstream state matching are case-insensitive. |

## `read_transposed_nexus`: lines 216–317

```python
216  def read_transposed_nexus(path: str | Path) -> Alignment:
217      """Read and validate a transposed nucleotide NEXUS matrix."""
218  
219      source = Path(path)
220      try:
221          raw = source.read_text(encoding="utf-8-sig")
222      except OSError as exc:
223          raise NexusFormatError(f"Could not read NEXUS file {source}: {exc}") from exc
224  
225      text = _strip_comments(raw)
226      if not re.search(r"^\s*#nexus\b", text, re.IGNORECASE):
227          raise NexusFormatError("File does not begin with #NEXUS.")
228      block = _find_data_block(text)
229      commands = _split_commands(block)
230  
231      dimensions: tuple[int, int] | None = None
232      format_values: tuple[str, str, str] | None = None
233      taxa: list[str] | None = None
234      matrix_command: tuple[str, int] | None = None
235  
236      for command, line_number in commands:
237          keyword_match = re.match(r"\s*([A-Za-z]+)", command)
238          if not keyword_match:
239              continue
240          keyword = keyword_match.group(1).lower()
241          body = command[keyword_match.end() :].strip()
242          if keyword == "dimensions":
243              if dimensions is not None:
244                  raise NexusFormatError("Multiple DIMENSIONS commands are not supported.")
245              dimensions = _parse_dimensions(body)
246          elif keyword == "format":
247              if format_values is not None:
248                  raise NexusFormatError("Multiple FORMAT commands are not supported.")
249              format_values = _parse_format(body)
250          elif keyword == "taxlabels":
251              if taxa is not None:
252                  raise NexusFormatError("Multiple TAXLABELS commands are not supported.")
253              taxa = _tokenize(body)
254          elif keyword == "matrix":
255              if matrix_command is not None:
256                  raise NexusFormatError("Multiple MATRIX commands are not supported.")
257              matrix_command = (body, line_number)
258  
259      if dimensions is None:
260          raise NexusFormatError("DATA block has no DIMENSIONS command.")
261      if format_values is None:
262          raise NexusFormatError("DATA block has no FORMAT command.")
263      if taxa is None:
264          raise NexusFormatError("DATA block has no TAXLABELS command.")
265      if matrix_command is None:
266          raise NexusFormatError("DATA block has no MATRIX command.")
267  
268      ntax, nchar = dimensions
269      gap, missing, symbols = format_values
270      if len(taxa) != ntax:
271          raise NexusFormatError(
272              f"TAXLABELS contains {len(taxa)} names, but NTAX declares {ntax}."
273          )
274      duplicates = sorted(name for name, count in Counter(taxa).items() if count > 1)
275      if duplicates:
276          preview = ", ".join(duplicates[:5])
277          raise NexusFormatError(f"Duplicate taxon label(s): {preview}.")
278  
279      matrix_body, matrix_line = matrix_command
280      sites: list[Site] = []
281      site_ids: set[str] = set()
282      allowed = _IUPAC | {gap.upper(), missing.upper()}
283      for offset, raw_line in enumerate(matrix_body.splitlines(), start=1):
284          if not raw_line.strip():
285              continue
286          tokens = _tokenize(raw_line)
287          if len(tokens) < 2:
288              raise NexusFormatError(
289                  f"Matrix row near line {matrix_line + offset} must contain a site label and states."
290              )
291          site_id = tokens[0]
292          if site_id in site_ids:
293              raise NexusFormatError(f"Duplicate matrix site identifier: {site_id}.")
294          states = _normalise_states(tokens[1:], ntax, len(sites) + 1)
295          invalid = sorted(set(states) - allowed)
296          if invalid:
297              raise NexusFormatError(
298                  f"Site {site_id} contains unsupported state symbol(s): {', '.join(invalid)}."
299              )
300          site_ids.add(site_id)
301          sites.append(Site(site_id=site_id, states=states, input_row=len(sites) + 1))
302  
303      if len(sites) != nchar:
304          raise NexusFormatError(
305              f"MATRIX contains {len(sites)} rows, but NCHAR declares {nchar}."
306          )
307  
308      return Alignment(
309          path=source,
310          taxa=tuple(taxa),
311          sites=tuple(sites),
312          ntax=ntax,
313          nchar=nchar,
314          gap=gap.upper(),
315          missing=missing.upper(),
316          symbols=symbols,
317      )
```

### File reading and block preparation: lines 216–229

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 216–217 | Defines the public reader and its purpose. | Accepts string or `Path`, returns `Alignment`. |
| 219 | Converts input to `Path`. | Stored in the resulting alignment. |
| 220–223 | Reads UTF-8 with optional BOM; wraps `OSError` as `NexusFormatError`. | Decode errors are not `OSError` and would propagate as `UnicodeError` in this version. |
| 225 | Removes comments. | Preserves line count for later diagnostics. |
| 226–227 | Requires `#NEXUS` at the beginning after optional whitespace. | A file with other leading non-whitespace text is rejected. |
| 228 | Extracts the one supported DATA/CHARACTERS block. | Other blocks are ignored. |
| 229 | Splits its contents into commands. | All trailing content must be semicolon-terminated. |

### Command collection: lines 231–257

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 231–234 | Initialises placeholders for each required command. | `None` distinguishes missing from parsed values. |
| 236 | Iterates command text with starting line. | Commands may appear in different orders. |
| 237–239 | Finds a leading alphabetic keyword; skips text without one. | Keyword matching is case-insensitive after lowercasing. |
| 240–241 | Separates keyword from body. | Parsers receive only arguments. |
| 242–245 | Parses one `DIMENSIONS`; rejects a second. | Duplicate required commands are not merged. |
| 246–249 | Parses one `FORMAT`; rejects a second. | Same strict duplicate policy. |
| 250–253 | Tokenises one `TAXLABELS`; rejects a second. | Taxon labels are kept in declared order. |
| 254–257 | Stores one `MATRIX` body and command start line; rejects a second. | Matrix parsing is deferred until all metadata is known. |
| — | Unknown commands are ignored. | This allows harmless extra commands in the supported block, but their semantics are not applied. |

### Required-command and taxon validation: lines 259–277

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 259–266 | Requires DIMENSIONS, FORMAT, TAXLABELS, and MATRIX. | Error identifies the missing command. |
| 268–269 | Unpacks dimensions and format values. | Establishes expected widths and special symbols. |
| 270–273 | Requires number of taxon labels to equal `NTAX`. | Prevents ambiguous state-to-taxon mapping. |
| 274 | Counts repeated taxon names and sorts duplicates. | Exact string comparison; case-sensitive names remain distinct. |
| 275–277 | Raises with up to five duplicate names. | Only the preview is truncated; validation rejects all duplicates. |

### Matrix rows: lines 279–301

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 279–282 | Initialises the matrix body, site list, unique-ID set, and allowed state set. | Allowed states are all built-in IUPAC symbols plus configured gap and missing symbols. |
| 283 | Iterates physical lines in the MATRIX body, with one-based offset. | Blank physical lines do not become sites. |
| 284–285 | Skips whitespace-only rows. | `NCHAR` is checked against retained rows. |
| 286 | Quote-aware tokenises the row. | First token is site ID; remaining tokens are states. |
| 287–290 | Requires at least site label plus state content. | Error uses approximate file line. |
| 291 | Takes first token as exact site identifier. | Quoted identifiers can contain spaces. |
| 292–293 | Rejects duplicate site IDs. | Avoids ambiguous output rows and coordinate references. |
| 294 | Normalises states using logical site number. | Produces uppercase string length `NTAX`. |
| 295 | Finds unsupported symbols by set difference and sorts them. | Error order is deterministic. |
| 296–299 | Rejects unsupported state symbols. | Symbols listed only in a custom SYMBOLS string are not automatically accepted. |
| 300–301 | Records ID and appends immutable `Site` with one-based `input_row`. | `input_row` counts nonblank matrix rows, not physical file lines. |

### Final dimension check and return: lines 303–317

| Line(s) | Literal effect | Detailed meaning |
|---|---|---|
| 303–306 | Requires actual site count to equal `NCHAR`. | Both missing and extra matrix rows are rejected. |
| 308–317 | Constructs immutable `Alignment`; uppercases gap/missing. | Preserves taxon and site order exactly as parsed. |

## Supported input contract inferred from the code

- One `BEGIN DATA;` or `BEGIN CHARACTERS;` block.
- Required `DIMENSIONS`, `FORMAT TRANSPOSE`, `TAXLABELS`, and `MATRIX`.
- Non-interleaved transposed matrix with one site per physical line.
- One compact state string or one single-character token per taxon.
- Canonical IUPAC symbols plus configured gap/missing.
- Exact unique taxon labels and exact unique site IDs.

## Tests most relevant to this chapter

`test_nexus.py` covers normal reading, compact rows, comments, non-transposed input, state-count errors, duplicate taxa/sites, explicit `INTERLEAVE=NO`, multiple data blocks, and unsupported `MATCHCHAR`/`EQUATE`. Chapter 09 lists the exact methods.
