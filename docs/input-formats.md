# Input formats

## Transposed NEXUS matrix

BRANCHSNV expects sites as rows and taxa as columns:

```nexus
#NEXUS
BEGIN DATA;
    DIMENSIONS NTAX=5 NCHAR=2;
    FORMAT SYMBOLS="ACGT" MISSING=? GAP=- TRANSPOSE;
    TAXLABELS Outgroup A B C D;
    MATRIX
        reference_100 G A A G G
        reference_200 C C C C C
    ;
END;
```

The first token on each matrix row is the site identifier. It is followed by
either:

- exactly `NTAX` single-character state tokens; or
- one compact string of length `NTAX`.

Quoted taxon and site labels are supported. A site identifier ending in
`_<integer>` is split into a `reference` and numeric `position` in the output.
This convenience parsing never replaces the original identifier.

### State symbols

Supported nucleotide symbols are:

```text
A C G T R Y S W K M B D H V N
```

The declared `MISSING` and `GAP` symbols are also accepted. During parsimony,
IUPAC codes are state sets and gap/missing are unknown among A/C/G/T. During
fixed-exclusive analysis, only A/C/G/T are callable.

### Deliberately unsupported NEXUS features

The current alpha rejects or does not implement:

- non-transposed matrices;
- interleaved matrices;
- multiple data or matrix blocks;
- matrix rows continued over multiple physical lines;
- polymorphism syntax such as `{AG}` or `(AG)`;
- equate directives;
- match-character expansion; and
- non-nucleotide alphabets.

Files should be converted upstream rather than relying on silent assumptions.

## Newick tree

Example:

```newick
(Outgroup:0.1,((A:0.01,B:0.01):0.02,(C:0.01,D:0.01):0.02):0.1);
```

BRANCHSNV supports:

- unique single-quoted or unquoted tip labels;
- optional internal labels;
- finite branch lengths, including scientific notation;
- comments in square brackets; and
- multifurcations.

Branch lengths are parsed and validated but are not used by equal-cost
parsimony.

A Newick string does not reliably communicate biological rooting by itself.
The CLI therefore requires an explicit outgroup or explicit acceptance of the
encoded root.

## Tip-list files

`--clade-tips` and `--outgroup-file` accept UTF-8 text with one exact taxon name
per line. Blank lines and lines beginning with `#` are ignored. Duplicate names
or whitespace within an unquoted name are rejected.
