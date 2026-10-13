# Reproducibility and asset availability

## Offline statistics: verified, no third-party downloads

Use Python 3.12.14 from the repository root:

```sh
python scripts/verify_results.py
```

This runs the two standard-library ports on saved counts and projected record metadata. It compares statistics, bootstrap draws and comparison CSVs byte-for-byte, writes only ignored `build/replayed/`, and invokes no encoder or network endpoint. The original calculations used Python 3.13.5; release-port replay was checked independently with 3.12.14 on Windows. JSON outputs explicitly retain the original CRLF serialization, CSV writers retain their standard CRLF dialect, and Git attributes disable evidence-file normalization. Other platforms have not been independently runtime-validated. Timing/script-hash verification sidecars differ intentionally; statistical outputs do not.

The synthetic port preserves the original 120-family manifest and uses only its 100 evaluation families for confirmatory summaries. The external port uses all 208 unique objects separately. Record text is unnecessary for this statistical replay. Exact stored SHA-256s, original script hashes and the declared filename/output-path changes are available in `configs/` and `results/release_verification.json`.

## External input recovery: pinned sources, exact hashes

If explicitly choosing to acquire the source inputs:

```sh
python scripts/fetch_assets.py --sources --output build/assets
python scripts/prepare_external_fixtures.py --cache build/assets/sources --output build/external-fixtures
```

Selected original source bodies total 506,856 bytes. Full conversation-containing trajectory bodies exist only in the ignored acquisition cache, not in the public tree or encoding fixture directory. The extractor reads explicit structured fields, applies the frozen code-bearing-argument exclusions and global semantic deduplication, retains exact values, and checks all 208 semantic hashes and 832 original serialization hashes. This recovery was verified in check-only mode against the already-local originals without writing new fixtures or invoking tokenizers.

Review upstream license notices and the two excluded simple-task code-bearing objects before redistribution. Do not stage cache contents. The project MIT license does not license MCP, A2A, SWE-agent or original program content.

## Optional encoding replay: requires assets and exact runtime

```sh
python scripts/fetch_assets.py --tokenizers --output build/assets
```

The four JSONs total 60,666,311 upstream LF bytes (60.67 MB), not model checkpoints. Each file must match its pinned upstream SHA-256 and size. The original Windows checkout SHA-256 differs because of CRLF conversion; both hashes are preserved, and the parsed model/derivative configurations match. No whole Git repository or tokenizer-training corpus is required.

Create an isolated Python 3.13.5 environment and install `requirements.txt`. If that exact interpreter is already active:

```sh
python -m venv .venv-encoding
```

Activate that environment using the command appropriate to your shell, then:

```sh
python -m pip install -r requirements.txt
python scripts/encode_fixtures.py --fixtures build/external-fixtures --assets-dir build/assets/tokenizers --output build/external-encoding.csv
```

The prepared direct-file wrapper enforces original and adapted configuration hashes, 200k core vocabulary, disabled dropout/padding/truncation/special insertion, whole-byte input, exact decode, deterministic IDs and original-adapter ID parity. It is a release port, not a byte-identical frozen script. It was syntax/CLI checked; **no encoding replay was executed during release preparation**. Its CSV is a fresh replay artifact and does not overwrite the frozen study. Frozen byte-boundary diagnostics remain in the preserved original package.

## Static vocabulary inventory: verified without encoding

After acquiring the tokenizer JSONs:

```sh
python scripts/audit_vocabulary.py --assets-dir build/assets/tokenizers --output build/vocabulary-audit.json
```

This standard-library script reproduces the already reported feature counts, including 893 versus zero colon-space types. It was verified against existing local asset snapshots; no new data or counts experiment was run.

## Synthetic input gate

The original 120 semantic objects, their serializations and the phrase-bearing generator remain intact privately. The owner explicitly chose to keep them private; they are excluded from this repository and its MIT license grant. Statistical reproduction from all 1,920 saved observations is already available. Full synthetic encoding reproduction requires authorized private access to the exact generator/fixtures. Do not reconstruct omitted inputs from narrative examples and call them the frozen dataset.

## Figures and Technical Note

To rebuild a figure from saved estimates, install `requirements-figures.txt` in an isolated plotting environment and run:

```sh
python scripts/plot_results.py --output build/figures
```

No bootstrap or encoding is repeated. The included figures come from the original measured datasets. The standalone note uses inline vector TikZ and ordinary LaTeX packages, with no external image input:

```sh
pdflatex -interaction=nonstopmode -halt-on-error -output-directory build docs/technical_note.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory build docs/technical_note.tex
```

Create `build/` first if it does not yet exist. The delivered PDF was compiled with installed MiKTeX 25.12 and visually checked at exactly two pages. The app compiler timed out; native compilation succeeded. Packages were not automatically installed. Final source/PDF hashes and numerical checks are recorded in `results/release_verification.json`.

## License and asset scope

Repository: [ZhijingWu/superbpe-serialization-evaluation](https://github.com/ZhijingWu/superbpe-serialization-evaluation).

The original included project materials are licensed under [MIT](../LICENSE), with the scope and upstream exclusions in [NOTICE](../NOTICE.md). The raw synthetic fixtures and generator remain private by explicit owner decision. Third-party tokenizer assets, raw schemas, trajectories and private reports are excluded. Optional downloaded assets remain governed by upstream terms and must stay in the ignored local cache.
