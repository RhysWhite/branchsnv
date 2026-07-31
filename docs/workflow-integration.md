# Workflow integration

## Shell validation

Run BRANCHSNV and then verify the deterministic report before allowing a
workflow to continue:

```bash
branchsnv find \
  --alignment core_snvs.nex \
  --tree rooted_tree.nwk \
  --outgroup outgroup_isolate \
  --clade-tips target_clade.txt \
  --mode both \
  --output results.tsv \
  --members-output members.txt \
  --report report.json

python examples/validate_report.py \
  --report report.json \
  --expected-descendants 42 \
  --minimum-reported-sites 1
```

The validator uses only the Python standard library.

## Snakemake

A minimal example is provided in `examples/snakemake/`. It demonstrates explicit
input, output, rooting, and branch-membership files. The branch member list is
an input rather than being reconstructed from a spreadsheet or visual tree.

## Reproducibility recommendations

- Version the NEXUS, Newick, and exact descendant-tip file together.
- Record upstream recombination and site filters.
- Use an explicit outgroup even when the tree appears visually rooted.
- Keep the TSV, membership file, and JSON report as one output set.
- Validate counts and checksums in the workflow rather than only checking that
  files exist.
- Do not update expected outputs automatically after a code change.
