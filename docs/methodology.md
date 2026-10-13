# Methodology

The original synthetic confirmatory analysis and external descriptive analysis remain separate. Only saved counts are replayed by the default verification command.

## Frozen synthetic pilot

Seed 1729 constructs 120 semantic families in four categories, 30 each: tool-call arguments, schemas, execution records and inter-agent messages. Five families/category are development-only; 25/category are held out. Five evaluation families/category carry a small Unicode slice. The generator uses ten schema shapes/category and related content siblings; the original ten-sentence phrase bank introduces additional dependence.

Four serializations use Python `json.dumps`, sorted keys, `ensure_ascii=False`, `allow_nan=False`, no trailing newline: compact `(',', ':')`, spaced `(', ', ': ')`, indent-2 `(',', ': ')` with indent 2, and tab-indent with one actual tab character. All versions parse to the same original object. Fixtures and implementation/statistical choices were frozen before counts.

The paired endpoint is `D = G_indent2 - G_compact`, `G = 1 - N_t180k/N_BPE`. Average families equally within category and the four categories equally. The 100 held-out families also have equal weight because categories are balanced. A paired category-stratified bootstrap resamples complete schema lineages within category, keeps all held-out siblings, and repeats 10,000 times with seed 6198. Percentile 95% intervals use linear interpolation. The preregistered practical margin is +/-0.05. The valid interval lies wholly above +0.05 within this fixture design.

## Separate public-artifact validation

The external set has 91 MCP schema definition objects, 93 A2A definition objects and 24 curated SWE-agent objects (18 explicit function arguments, six execution states). Its runtime records cover only two benchmark tasks. Existing values, array order and `$ref` strings were preserved, with full source schemas retaining reference context outside the public tree. Global semantic deduplication removed 37 repeated objects; two code-bearing arguments were excluded before counts because their underlying program's reuse license was unverified. No postfreeze exclusions occurred.

Whole-group bootstrapping uses ten coarse MCP groups, eight A2A groups and two task lineages. Resample within source, preserve paired conditions, then average the three source means equally. The same 10,000/6198 percentile settings apply, but the external summary is descriptive and conditional on these selected groups/sources. The two-task interval is not evidence of 24 independent runs. Source-composition ranges and leave-one-source/lineage results are descriptive sensitivities, not deployment-population inference.

## Assets and adapter

All four official assets have 200,000 core vocabulary entries and are pinned to repository commit `bbd09768fc28a875cef48e6bdd66e3a17454628e`. Primary: BPE 200k and SuperBPE t180k. Sensitivities: t80k and no-whitespace 200k. In-memory removal of added tokens and assignment of a ByteLevel decoder preserve all measured encoded IDs. Original normalizers, pretokenizers, vocabularies and merge ranks stay intact. Dropout, padding, truncation and special-token insertion are disabled; `ignore_merges=False`.

The audit used Python 3.13.5 and upstream tokenizers 0.20.3 with direct whole-record encoding. It did not use the original paragraph-splitting CLI. All original 5,248 tokenizer observations passed exact decode, deterministic repetition, adapter-ID parity and byte reconstruction. Repetition verifies correctness, not statistical independence. Full custom-fork parity and complete historical training-byte identity remain unverified.

## Metrics and public projections

Absolute savings are `N_baseline-N_comparison`. Family-average G is an arithmetic mean of per-object ratios. Corpus G is `1-sum(N_comparison)/sum(N_baseline)`, with format-dependent baseline weights. Negative G means the comparison uses more tokens. Bytes/token and code points/token are distinct and saved separately.

Public record manifests retain analysis-needed categorical/lineage/length metadata and hashes without raw values or local paths. Numerical CSVs and aggregate files are copied byte-for-byte. All development, held-out, sensitivity and regression observations remain; omission of raw text from the public tree is a disclosed redistribution decision, not a scientific sample exclusion. Original script/protocol hashes and release derivations are in `configs/`.
