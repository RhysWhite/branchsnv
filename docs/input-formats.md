# Input formats

## NEXUS matrix

BRANCHSNV accepts nucleotide NEXUS matrices in conventional
taxon-by-character or transposed character-by-taxon orientation:

### Transposed orientation

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

`TRANSPOSE`, `TRANSPOSE=YES`, or `TRANSPOSE=TRUE` identifies this orientation.
`TAXLABELS` is required because taxa are represented as matrix columns.

The first token on each matrix row is the site identifier. It is followed by
either:

- exactly `NTAX` single-character state tokens; or
- one compact string of length `NTAX`.

### Conventional orientation

Without `TRANSPOSE`, or with `TRANSPOSE=NO` or `TRANSPOSE=FALSE`, taxa are rows and characters are columns:

```nexus
#NEXUS
BEGIN DATA;
    DIMENSIONS NTAX=5 NCHAR=2;
    FORMAT SYMBOLS="ACGT" MISSING=? GAP=-;
    TAXLABELS Outgroup A B C D;
    CHARLABELS reference_100 reference_200;
    MATRIX
        Outgroup GC
        A        AC
        B        AC
        C        GC
        D        GC
    ;
END;
```

Each matrix row begins with a taxon label followed by either one compact sequence of length `NCHAR` or exactly `NCHAR` single-character state tokens.

`TAXLABELS` is optional for conventional matrices. When present, it must contain exactly the same taxon set as the matrix and defines the normalized taxon order. When absent, matrix-row order is used.

`CHARLABELS` is optional for conventional matrices. When present, it supplies site identifiers in character order. When absent, BRANCHSNV assigns deterministic one-based identifiers (`1`, `2`, ..., `NCHAR`). These are alignment character numbers only and are not interpreted as genomic coordinates.

Quoted taxon and site labels are supported. Empty labels are rejected. If the
`FORMAT` command declares `DATATYPE`, it must be `DNA` or `NUCLEOTIDE`; omitting
`DATATYPE` remains supported when the matrix otherwise satisfies the nucleotide
input contract. A site identifier ending in `_<integer>` is split into a
`reference` and numeric `position` in the output. This convenience parsing never
replaces the original identifier.

### State symbols

Supported nucleotide symbols are:

```text
A C G T R Y S W K M B D H V N
```

The declared `MISSING` and `GAP` symbols are also accepted. Each must be one
character, they must differ case-insensitively, and neither may overlap a
supported nucleotide/IUPAC symbol. During parsimony, IUPAC codes are state sets
and gap/missing are unknown among A/C/G/T. During fixed-exclusive analysis, only
A/C/G/T are callable.

### Deliberately unsupported NEXUS features

BRANCHSNV currently rejects or does not implement:

- interleaved matrices;
- multiple data or matrix blocks;
- matrix rows continued over multiple physical lines;
- `CHARSTATELABELS`;
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

- unique, non-empty single-quoted or unquoted tip labels without line breaks;
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
per line. Leading and trailing whitespace is stripped. Blank lines and lines that
begin with `#` after stripping are ignored. Internal whitespace is preserved as
part of the taxon name, and duplicate names are rejected.
