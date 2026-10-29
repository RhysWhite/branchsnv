# Related publications and tools

These links provide context and directly connected validation evidence. They
are **not** implicit software dependencies, and including a tool here does not
mean BRANCHSNV has independently benchmarked it.

## Directly compared in the validation repository

- **SNPPar:** Edwards DJ, Duchêne S, Pope B, Holt KE. *SNPPar: identifying
  convergent evolution and other homoplasies from microbial whole-genome
  alignments*. *Microbial Genomics* (2021).
  [Paper](https://doi.org/10.1099/mgen.0.000694) ·
  [software](https://github.com/d-j-e/SNPPar) ·
  [published test inputs](https://github.com/d-j-e/SNPPar_test).
  BRANCHSNV Experiment 03 is a conditional event-concordance comparison;
  SNPPar and BRANCHSNV are **not** interchangeable implementations.

## Published focal-branch data (Experiment 05)

- MRSA AK3 — White et al., *Microbial Genomics* (2025).
  [Paper](https://doi.org/10.1099/mgen.0.001452).
- MRSA ST97 NICU — White et al., *Microbial Genomics* (2024).
  [Paper](https://doi.org/10.1099/mgen.0.001273).
- *E. coli* ST131 / OXA-48 — White et al., *Drug Resistance Updates*
  (2026). [Paper](https://doi.org/10.1016/j.drup.2025.101327).

The exact comparison inputs and 46 prespecified SNVs are documented in
[Experiment 05](https://github.com/RhysWhite/branchsnv-validation/tree/main/experiments/05_published_focal_branches).

## Upstream analysis context (not BRANCHSNV functions)

- **Gubbins:** Croucher et al., *Rapid phylogenetic analysis of large samples
  of recombinant bacterial whole genome sequences using Gubbins*.
  [Paper](https://doi.org/10.1093/nar/gku1196) ·
  [software](https://github.com/sanger-pathogens/Gubbins). Recombination analysis
  must be performed upstream where appropriate.
- **IQ-TREE 2:** Minh et al., *IQ-TREE 2: New models and efficient methods for
  phylogenetic inference in the genomic era*.
  [Paper](https://doi.org/10.1093/molbev/msaa015) ·
  [software](https://github.com/iqtree/iqtree2). BRANCHSNV takes an existing
  rooted tree and does not infer one.

For **which input files were actually used**, consult the validation
[third-party attribution](https://github.com/RhysWhite/branchsnv-validation/blob/main/THIRD_PARTY.md)
and experiment-level manifests. These contextual links must not be confused
with the benchmark's exact method list or a software-dependency list.
