# Observational mechanism evidence

The paper's Appendix A.1.4 already describes excluding tokens containing colon followed by ASCII space. Its [FAQ](https://superbpe.github.io/faq.html) and [issue 9](https://github.com/PythonNut/superbpe/issues/9) discuss stage-specific regex and punctuation/newline behavior. This evaluation quantifies released-asset behavior; it does not discover an undocumented bug.

The released t180k and no-whitespace assets have identical inference pretokenizers, null normalizers and non-vocabulary model settings. They share only 32,883 of 200,000 byte-token strings. A post-count descriptive vocabulary inspection finds 893 colon-space token types in no-whitespace and none in t180k, t80k or BPE. Similar directory suffixes do not establish identical training constraints.

Original byte-reconstructed token partitions were aligned at positions that are boundaries in both tokenizations. Local `N_t180k-N_noWhitespace` gaps conserve the whole-record difference on all 832 external record/format pairs. The aggregate accounting is retained without redistributing the source text or token-byte streams.

| Format | Structural only | Mixed LF/tab | Mixed structural space | Mixed JSON punctuation | String content/other | Net gap |
|---|---:|---:|---:|---:|---:|---:|
| Compact | -1,734 | 0 | 0 | -1,111 | -318 | -3,163 |
| Spaced | 696 | 0 | 1,115 | -12 | -90 | 1,709 |
| Indent-2 | 1,653 | 487 | 2,445 | -1 | -95 | 4,489 |
| Tab-indent | 3,249 | 803 | 2,585 | 61 | -95 | 6,603 |

These exclusive accounting classes follow a fixed hierarchy; feature occurrence diagnostics overlap. Quoted keys and values both count as string content. Escaped newline characters inside a value differ from actual formatting LF. Regions containing structural colon-space carry 3,335 of the indent-2 4,489-token net gap, but also contain other bytes. This is not a causal percentage allocation to one training rule.

t180k's external crossing-token fraction rises from 8.40% compact to 35.04% indent-2; no-whitespace rises from 26.23% to 62.59%. No-whitespace has more crossings even where its compact count is worse. Crossing frequency alone cannot explain efficiency.

`scripts/audit_vocabulary.py` can reproduce the static feature counts after acquiring the pinned tokenizer JSONs. Exact partition accounting remains part of the preserved private evidence; the public numerical accounting tables are byte-identical. No boundary intervention or model modification occurred in this stage.
