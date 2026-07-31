# AK3 working-dataset validation

This directory records a real-data validation using the working files supplied
for development of BRANCHSNV. The large alignment and tree are not duplicated
in the repository.

## Required external files

| File | SHA-256 |
|---|---|
| `396_MRSA_AK3(1).nex` | `40c49b026c52e04530ecbbee7044567ac3355eccf7adda42a7d96bf977df9014` |
| `Cluster_1_396genomes_refsa230905_barcode06_ML_Flitered_BS.nwk` | `18322b2808baf621d09dd5292027205e68a0f207d7be44f043bd044d0d314bd0` |

The input pair contains 396 exactly matched taxa and 10,481 transposed matrix
rows. The tree is rooted using `SRR13968194`.

## Recorded branches

- `sapi_385_tips.txt`: exact membership of the 385-descendant working branch.
- `mrsa_360_tips.txt`: exact membership of the 360-descendant MRSA AK3 branch.

Membership, not descendant count alone, defines each branch.

## Expected working-file results

The 360-descendant branch produces 23 SNV rows, matching the SNV positions in
the published MRSA AK3 branch table. The published deletion is outside the
scope of the current BRANCHSNV alpha.

The 385-descendant branch produces 15 SNV rows. Fourteen coordinates overlap
the published SaPITokyo12571-like branch table's SNV rows; coordinate 1,891,191
is additionally present in the supplied working inputs. The nucleotide
directions in the working matrix differ from the corresponding published table
entries. These observations are documented as an unresolved input/publication
version difference rather than being changed to force agreement.

## Run the validation

```bash
bash validation/ak3/run_validation.sh \
  /path/to/396_MRSA_AK3\(1\).nex \
  /path/to/Cluster_1_396genomes_refsa230905_barcode06_ML_Flitered_BS.nwk
```

The script verifies both input checksums before running BRANCHSNV and compares
the produced TSVs byte-for-byte with the committed expected outputs.
