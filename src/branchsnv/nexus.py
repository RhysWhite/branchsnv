"""Strict parser for the transposed nucleotide NEXUS subset used by BRANCHSNV."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .errors import NexusFormatError
from .models import Alignment, Site

_IUPAC = frozenset("ACGTRYSWKMBDHVN")


def _strip_comments(text: str) -> str:
    """Remove nested NEXUS comments while preserving line breaks and quoted text."""

    output: list[str] = []
    depth = 0
    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            output.append(char if depth == 0 else ("\n" if char == "\n" else " "))
            if char == quote:
                # NEXUS single-quoted strings escape a quote by doubling it.
                if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
                    index += 1
                    output.append(text[index] if depth == 0 else " ")
                else:
                    quote = None
            index += 1
            continue

        if depth == 0 and char in {"'", '"'}:
            quote = char
            output.append(char)
        elif char == "[":
            depth += 1
            output.append(" ")
        elif char == "]" and depth:
            depth -= 1
            output.append(" ")
        elif depth:
            output.append("\n" if char == "\n" else " ")
        else:
            output.append(char)
        index += 1

    if depth:
        raise NexusFormatError("Unterminated NEXUS comment.")
    if quote is not None:
        raise NexusFormatError("Unterminated quoted string in NEXUS file.")
    return "".join(output)


def _split_commands(text: str) -> list[tuple[str, int]]:
    """Split a NEXUS block into semicolon-terminated commands."""

    commands: list[tuple[str, int]] = []
    start = 0
    line = 1
    start_line = 1
    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            if char == quote:
                if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
                    index += 1
                else:
                    quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char == ";":
            command = text[start:index].strip()
            if command:
                commands.append((command, start_line))
            start = index + 1
            start_line = line
        if char == "\n":
            line += 1
            if start == index + 1:
                start_line = line
        index += 1

    if text[start:].strip():
        raise NexusFormatError("NEXUS command is not terminated by a semicolon.")
    return commands


def _unquote(token: str) -> str:
    token = token.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        inner = token[1:-1]
        if token[0] == "'":
            return inner.replace("''", "'")
        return inner
    return token


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            current.append(char)
            if char == quote:
                if quote == "'" and index + 1 < len(text) and text[index + 1] == "'":
                    index += 1
                    current.append(text[index])
                else:
                    quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char.isspace():
            if current:
                tokens.append(_unquote("".join(current)))
                current = []
        else:
            current.append(char)
        index += 1
    if quote is not None:
        raise NexusFormatError("Unterminated quoted token.")
    if current:
        tokens.append(_unquote("".join(current)))
    return tokens


def _find_data_block(text: str) -> str:
    pattern = re.compile(r"\bbegin\s+(data|characters)\s*;", re.IGNORECASE)
    matches = list(pattern.finditer(text))
    if not matches:
        raise NexusFormatError("No BEGIN DATA or BEGIN CHARACTERS block was found.")
    if len(matches) > 1:
        raise NexusFormatError("Multiple DATA/CHARACTERS blocks are not supported.")
    match = matches[0]
    remainder = text[match.end() :]
    end_match = re.search(r"\bend(?:block)?\s*;", remainder, re.IGNORECASE)
    if not end_match:
        raise NexusFormatError("The DATA block has no terminating END; statement.")
    return remainder[: end_match.start()]


def _parse_dimensions(command: str) -> tuple[int, int]:
    ntax_match = re.search(r"\bntax\s*=\s*(\d+)", command, re.IGNORECASE)
    nchar_match = re.search(r"\bnchar\s*=\s*(\d+)", command, re.IGNORECASE)
    if not ntax_match or not nchar_match:
        raise NexusFormatError("DIMENSIONS must declare both NTAX and NCHAR.")
    ntax = int(ntax_match.group(1))
    nchar = int(nchar_match.group(1))
    if ntax < 1 or nchar < 1:
        raise NexusFormatError("NTAX and NCHAR must both be positive integers.")
    return ntax, nchar


def _parse_format(command: str) -> tuple[str, str, str]:
    transpose_match = re.search(
        r"\btranspose\b(?:\s*=\s*([^\s]+))?", command, re.IGNORECASE
    )
    if not transpose_match:
        raise NexusFormatError("BRANCHSNV requires FORMAT TRANSPOSE.")
    transpose_value = transpose_match.group(1)
    if transpose_value is not None and _unquote(transpose_value).lower() not in {
        "yes",
        "true",
    }:
        raise NexusFormatError("BRANCHSNV requires FORMAT TRANSPOSE or TRANSPOSE=YES.")
    interleave_match = re.search(
        r"\binterleave\b(?:\s*=\s*([^\s]+))?", command, re.IGNORECASE
    )
    if interleave_match:
        value = interleave_match.group(1)
        if value is None or _unquote(value).lower() not in {"no", "false"}:
            raise NexusFormatError("Interleaved matrices are not supported.")
    if re.search(r"\bmatchchar\s*=", command, re.IGNORECASE):
        raise NexusFormatError("FORMAT MATCHCHAR is not supported.")
    if re.search(r"\bequate\s*=", command, re.IGNORECASE):
        raise NexusFormatError("FORMAT EQUATE is not supported.")

    gap_match = re.search(r"\bgap\s*=\s*([^\s]+)", command, re.IGNORECASE)
    missing_match = re.search(r"\bmissing\s*=\s*([^\s]+)", command, re.IGNORECASE)
    symbols_match = re.search(
        r"\bsymbols\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s]+))",
        command,
        re.IGNORECASE,
    )
    gap = _unquote(gap_match.group(1)) if gap_match else "-"
    missing = _unquote(missing_match.group(1)) if missing_match else "?"
    if symbols_match:
        symbols = next(group for group in symbols_match.groups() if group is not None)
    else:
        symbols = "ACGT"
    symbols = "".join(dict.fromkeys(symbols.upper()))
    if not set("ACGT").issubset(set(symbols)):
        raise NexusFormatError("FORMAT SYMBOLS must include A, C, G, and T.")
    if len(gap) != 1 or len(missing) != 1:
        raise NexusFormatError("GAP and MISSING symbols must each be one character.")
    gap_upper = gap.upper()
    missing_upper = missing.upper()
    if gap_upper == missing_upper:
        raise NexusFormatError("GAP and MISSING symbols must differ.")
    if gap_upper in _IUPAC or missing_upper in _IUPAC:
        raise NexusFormatError(
            "GAP and MISSING symbols must not overlap supported nucleotide/IUPAC symbols."
        )
    return gap, missing, symbols


def _normalise_states(tokens: list[str], ntax: int, row_number: int) -> str:
    if len(tokens) == 1 and len(tokens[0]) == ntax:
        states = tokens[0]
    elif len(tokens) == ntax and all(len(token) == 1 for token in tokens):
        states = "".join(tokens)
    else:
        raise NexusFormatError(
            f"Matrix row {row_number} has {len(tokens)} state token(s); expected "
            f"{ntax} single-character states or one compact string of length {ntax}."
        )
    return states.upper()


def read_transposed_nexus(path: str | Path) -> Alignment:
    """Read and validate a transposed nucleotide NEXUS matrix."""

    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8-sig")
    except UnicodeError as exc:
        raise NexusFormatError(
            f"Could not decode NEXUS file {source} as UTF-8: {exc}"
        ) from exc
    except OSError as exc:
        raise NexusFormatError(f"Could not read NEXUS file {source}: {exc}") from exc

    text = _strip_comments(raw)
    if not re.search(r"^\s*#nexus\b", text, re.IGNORECASE):
        raise NexusFormatError("File does not begin with #NEXUS.")
    block = _find_data_block(text)
    commands = _split_commands(block)

    dimensions: tuple[int, int] | None = None
    format_values: tuple[str, str, str] | None = None
    taxa: list[str] | None = None
    matrix_command: tuple[str, int] | None = None

    for command, line_number in commands:
        keyword_match = re.match(r"\s*([A-Za-z]+)", command)
        if not keyword_match:
            continue
        keyword = keyword_match.group(1).lower()
        body = command[keyword_match.end() :].strip()
        if keyword == "dimensions":
            if dimensions is not None:
                raise NexusFormatError("Multiple DIMENSIONS commands are not supported.")
            dimensions = _parse_dimensions(body)
        elif keyword == "format":
            if format_values is not None:
                raise NexusFormatError("Multiple FORMAT commands are not supported.")
            format_values = _parse_format(body)
        elif keyword == "taxlabels":
            if taxa is not None:
                raise NexusFormatError("Multiple TAXLABELS commands are not supported.")
            taxa = _tokenize(body)
        elif keyword == "matrix":
            if matrix_command is not None:
                raise NexusFormatError("Multiple MATRIX commands are not supported.")
            matrix_command = (body, line_number)

    if dimensions is None:
        raise NexusFormatError("DATA block has no DIMENSIONS command.")
    if format_values is None:
        raise NexusFormatError("DATA block has no FORMAT command.")
    if taxa is None:
        raise NexusFormatError("DATA block has no TAXLABELS command.")
    if matrix_command is None:
        raise NexusFormatError("DATA block has no MATRIX command.")

    ntax, nchar = dimensions
    gap, missing, symbols = format_values
    if len(taxa) != ntax:
        raise NexusFormatError(
            f"TAXLABELS contains {len(taxa)} names, but NTAX declares {ntax}."
        )
    duplicates = sorted(name for name, count in Counter(taxa).items() if count > 1)
    if duplicates:
        preview = ", ".join(duplicates[:5])
        raise NexusFormatError(f"Duplicate taxon label(s): {preview}.")

    matrix_body, matrix_line = matrix_command
    sites: list[Site] = []
    site_ids: set[str] = set()
    allowed = _IUPAC | {gap.upper(), missing.upper()}
    for offset, raw_line in enumerate(matrix_body.splitlines(), start=1):
        if not raw_line.strip():
            continue
        tokens = _tokenize(raw_line)
        if len(tokens) < 2:
            raise NexusFormatError(
                f"Matrix row near line {matrix_line + offset} must contain a site label and states."
            )
        site_id = tokens[0]
        if site_id in site_ids:
            raise NexusFormatError(f"Duplicate matrix site identifier: {site_id}.")
        states = _normalise_states(tokens[1:], ntax, len(sites) + 1)
        invalid = sorted(set(states) - allowed)
        if invalid:
            raise NexusFormatError(
                f"Site {site_id} contains unsupported state symbol(s): {', '.join(invalid)}."
            )
        site_ids.add(site_id)
        sites.append(Site(site_id=site_id, states=states, input_row=len(sites) + 1))

    if len(sites) != nchar:
        raise NexusFormatError(
            f"MATRIX contains {len(sites)} rows, but NCHAR declares {nchar}."
        )

    return Alignment(
        path=source,
        taxa=tuple(taxa),
        sites=tuple(sites),
        ntax=ntax,
        nchar=nchar,
        gap=gap.upper(),
        missing=missing.upper(),
        symbols=symbols,
    )
