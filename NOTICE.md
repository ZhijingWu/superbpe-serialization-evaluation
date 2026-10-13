# Attribution and license scope

This independent evaluation is authored by Zhijing Wu with AI assistance. It is not affiliated with the University of Washington or the original SuperBPE research team.

Alisa Liu, Jonathan Hayase, Valentin Hofmann, Sewoong Oh, Noah A. Smith and Yejin Choi contributed **SuperBPE: Space Travel for Language Models**, arXiv:2503.13423v3 (COLM 2025 camera-ready). Their project introduced the two-stage tokenization curriculum and evaluated trained language models. This repository contributes fixed-released-tokenizer serialization measurements; it does not reproduce their LM experiments. See the [paper](https://arxiv.org/abs/2503.13423v3), [project](https://superbpe.github.io/), and [pinned release](https://github.com/PythonNut/superbpe/tree/bbd09768fc28a875cef48e6bdd66e3a17454628e).

Upstream MCP, A2A, SWE-agent and Marshmallow projects supplied the public schema/example sources evaluated here. Exact revisions, URLs, declared rights and download hashes are in [configs/sources.json](configs/sources.json). The MCP snapshot has an explicit MIT-to-Apache licensing transition; the checked license, not its stale README or a guessed SPDX label, governs reuse. A2A is Apache-2.0; SWE-agent and the inspected Marshmallow code are MIT. No raw schemas, program fragments or complete conversations are bundled.

Original tokenizer assets, third-party datasets and library packages keep their own rights. Linking to them does not relicense them. Optional acquisition writes into an ignored local cache. No training corpus or model checkpoint is distributed.

## MIT scope

The root [LICENSE](LICENSE) applies to the original project code, documentation, Technical Note, figures, and original analysis materials included in this repository, to the extent Zhijing Wu holds the rights to license them. AI assistance was used in implementation and drafting. The license does not assert exclusive rights over facts, measurements, public identifiers, or other uncopyrightable material.

Third-party works, cited quotations and illustrative source text, linked assets, source-derived metadata, dependencies, and embedded fonts retain their applicable upstream rights and terms. No license to the original SuperBPE paper, tokenizer vocabularies, training text, MCP/A2A schemas, SWE-agent trajectories, or underlying program content is granted by this project's MIT license. Attribution and links identify provenance; they do not transfer those rights.

By the owner's explicit publication decision, the raw synthetic fixtures and their phrase-bearing generator remain private and are excluded from this repository and its license grant. Third-party raw assets and private reports are also excluded. Full synthetic re-encoding therefore requires authorized private access; saved-count statistical replay is available here.
