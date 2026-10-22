# RNA Evidence Agent

A solo Open Agent Hackathon build. The goal is to answer questions about public RNA-seq data with reproducible calculations, visible evidence, and dataset-scoped memory.

## What exists

- A Python wrapper around the declared pre-existing RNA-seq Agent.
- A Meterless H-MEM subprocess bridge with per-dataset persistence, provenance, feedback and audit access.
- A local Zetaris connector restricted to an explicit table catalog and bounded read queries.
- A deterministic input inventory that checks count values, sample identifiers and file hashes.
- A read-only local progress dashboard.

Three real Codex-backed demonstrations ran on a checked Zetaris export: dataset inventory, raw-count depth QC with error recovery, and paired-design clarification. Their 34 registered output references match successful Python stdout. This is traceability for these demonstrations, not a reliability score or scientific validation. Meterless persisted run pointers; one exact repeated question retrieved a prior pointer. Broad semantic recall is not established.

## Baseline disclosure

`baseline_manifest.json` records the pre-event RNA-seq Agent. Its agent loop, prompts, tool executor, datasets and earlier results are existing work. New work in this directory began during the build window. Earlier benchmark scores are not scores for this integration.

Meterless reference commit: `1742dec56a66e58eef9dda2d2b865823758ca8cd`. The upstream reference is Apache-2.0. It is imported from the separate infrastructure checkout and has not been copied or modified here.

## Run

Use Python 3.11+ and Node 24 with TypeScript transformation support. Install the project with its `analysis` extra in a dedicated environment. Set these environment variables privately:

- `HMEM_REFERENCE`: path to the pinned `engines/hmem/reference` directory.
- `RNA_NODE`: Node executable, if it is not on PATH.
- Nightshift runtime: required for the default backend, with a real runtime token. Codex remains an explicitly selected historical-demo option.
- `ANTHROPIC_API_KEY`: optional; used only with `--backend anthropic`. Never commit it.

The existing agent's `host.llm` backend requires a host-provided callable; it is not automatically available in an ordinary Python process. This build does not pretend otherwise.

```
rna-evidence-agent \
  --baseline /absolute/path/to/rnaseq_agent \
  --counts /absolute/path/to/expression_counts.csv \
  --metadata /absolute/path/to/sample_metadata.csv \
  --run-dir runs/new-run \
  --backend codex \
  --question "How many genes and samples are in these files?"
```

The baseline executor runs generated Python in a subprocess, not a security sandbox. Use trusted public datasets and an isolated environment. Do not expose execution through the dashboard.

## Evidence

Each completed run stores a transcript, dataset fingerprint and evidence manifest. Prior memories are untrusted context. The prompt requires recomputation from the current files. Memory capture stores an unreviewed run pointer, not an endorsed conclusion. This requirement is not a guarantee that every generated claim is correct.

Full local demonstration artifacts are ignored by Git under `runs/`; sanitized result summaries are provided in `output_examples/`. The live runs used the full checked RNA export, not the initial five-row platform connectivity example.

## Submission status

The earlier entry was submitted on October 22. The Nightshift revision below adds the bounded explanation feature. Updating source files does not update the submitted entry automatically. Prior software checks and historical Codex examples do not validate the new Nightshift code.

## Install locally

The offline sample needs Python 3.11+ and no third-party Python packages. The live path currently supports macOS/Linux (the memory adapter uses `fcntl`), Node 24, Git, and an installed, authenticated Codex CLI. Install dependencies before the live run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[analysis]'
mkdir -p .vendor
git clone https://github.com/brhanufen/rnaseq-agent.git .vendor/rnaseq-agent
git -C .vendor/rnaseq-agent checkout f0b727f948e5c679c4967842f65df5fa5f411370
.venv/bin/python -m pip install -e .vendor/rnaseq-agent
git clone https://github.com/Meterless/Meterless.git .vendor/meterless
git -C .vendor/meterless checkout 1742dec56a66e58eef9dda2d2b865823758ca8cd
```

Set `HMEM_REFERENCE` to the pinned Meterless checkout's `engines/hmem/reference` directory at commit `1742dec56a66e58eef9dda2d2b865823758ca8cd`, and `RNA_NODE` if Node is not on PATH. Zetaris itself requires the separately configured local platform; the sample fallback does not require it.

Run focused checks with `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`.

## Offline examples

The technical requirements call for a network-free sample path. `run.py` implements three deterministic operations over four synthetic genes and four samples. This is explicitly a fallback demonstration, not an LLM simulation.

```
python run.py --input input_examples/example_1.json
```

`input_examples/` and `output_examples/` contain three matching requests and real generated outputs: inventory, sample counts by group, and a fixed unsupported-claim scenario. Run IDs are immutable; use a new ID when repeating an example. Traces go to stderr and `logs/`.

Zetaris credentials are runtime environment variables only: `ZETARIS_USERNAME` and `ZETARIS_PASSWORD`. The earlier private local connectivity demonstration loaded existing platform credentials in a transient launcher; those values are not part of this project.

The offline image was built and its inventory example executed as a nonroot user with `--network none`. The base image digest is pinned in `Dockerfile.sample`. This establishes the sample path only; it does not establish live model or RNA-Zetaris integration.

```
docker build -f Dockerfile.sample -t rna-evidence-agent-sample .
docker run --rm --network none rna-evidence-agent-sample
```

## RNA data through Zetaris

The local `RNA_EVIDENCE_2026` database now has `counts` and `metadata` REST tables. Their source is a nonroot read-only container on the private `zetaris_default` Docker network, with no host port published. The source serves only the two declared CSVs. Local filestore registration was rejected by Zetaris, so it was not used.

`scripts/register_rna.py` prints the two explicit registration statements by default; `--apply` performs them and requires the database to exist. It is not an idempotent migration. `scripts/export_rna.py --output runs/new-snapshot` exports through Zetaris and checks row counts against independent count queries before writing the source manifest.

The first full export contained 21,833 gene rows and 8 metadata rows. Every identifier and cell value matched the source CSVs. Sorting and CSV encoding changed, so byte hashes differ. The source snapshot and comparison are retained under `runs/zetaris_rna_snapshot_01/`. A live Codex-backed inventory has now run on this export.

`run_live.py` invokes the live CLI with a ten-minute process-group deadline. Use `--source-manifest runs/zetaris_rna_snapshot_01/source_manifest.json` to include Zetaris provenance in the agent run. Credentials are inherited from the environment, not command-line arguments.

## Codex local backend

The optional `--backend codex` backend calls the installed `codex exec` with a read-only sandbox, temporary session, and a JSON output schema. It requests only the next analysis script or final answer. The existing RNA agent executes the script and feeds its output into the next model call. The adapter does not read or copy authentication credentials. It uses the operator's existing Codex login and usage limits; judges would need their own authorized login. This is a local demonstration option, not a shared hosted API credential.

Official interface documentation: https://learn.chatgpt.com/docs/non-interactive-mode

## Live demonstration results

Three Codex-backed runs used the checked Zetaris export: inventory (3 steps, no execution errors, 59.90 seconds), raw-depth QC (5 steps, 2 execution errors, 166.14 seconds), and paired-design inspection (3 steps, no execution errors, 42.60 seconds). The QC run recovered from missing matplotlib and a glyph bug, then produced its PNG. Both errors remain in its transcript.

Across these runs, 34 explicitly registered claim references matched successful Python output. This establishes reference linkage only for those claims, not complete free-text coverage, method correctness or a general success rate. These were one-off demonstrations, not a held-out benchmark. Sanitized summaries are in `output_examples/codex_live_*.json`; full local traces are under `runs/`.

The dedicated `.venv` now includes the declared baseline and analysis dependencies, including matplotlib. `environment.json` records the local versions. The earlier QC failures remain part of the original demonstration. A separate presentation figure was recomputed with matplotlib under `runs/presentation_figure_01/`; it does not replace the agent's original chart or transcript.

A subsequent repeat of the inventory question retrieved one prior run pointer through H-MEM. The first three distinct live questions retrieved no prior records. This demonstrates narrow repeated-question recall, not broad semantic retrieval.

## Development and licensing

Cursor made the recorded-viewer labeling and navigation edits, documented in `cursor_contribution.json`. Codex implemented the integration and review fixes. The existing RNA-seq engine is MIT licensed; Meterless is Apache-2.0 and remains a separately pinned dependency. Their licenses remain with their repositories. This integration is MIT licensed. Public GEO data provenance is in the source manifest; the committed offline fixture is synthetic and CC0.

The live wheel includes the TypeScript memory bridge. Use `run_live.py` from the source checkout for the ten-minute overall deadline. Direct CLI invocation has per-model-call timeouts but not that overall process-group deadline.

## Review artifacts

`review_status.json` records the completed checks and remaining limitations. The wheel builds, includes its TypeScript bridge, and installs into a fresh environment; CLI help works. All three offline examples also pass from an isolated source copy. These checks do not establish an end-to-end live installation on a second machine.

The optional macOS media builder is `scripts/build_walkthrough.py`; it needs Pillow and imageio-ffmpeg, the system speech service, and the locally retained public demo artifacts and slide renders. Media-building dependencies are not runtime requirements of the agent.

## Inspect the recorded examples

From the source checkout, run `PYTHONPATH=src python -m rna_evidence_agent.server` and open `http://127.0.0.1:8787/` in your own local browser. The viewer uses full local run records when available, otherwise the committed sanitized `output_examples/codex_live_*.json` files. It never triggers analysis over HTTP. Sanitized examples omit local execution code and figures. This source-checkout viewer is separate from the installed analysis CLI.

## Paired-design decision workflow

A new deterministic review gate checks sample alignment and whether each `cell_line` has exactly one control and one treated sample. It proposes `~ cell_line + group` only as a candidate, and asks the researcher to confirm that the factor represents the biological experimental unit. It does not infer biological validity from labels or fit differential expression.

```sh
rna-evidence-agent --baseline .vendor/rnaseq-agent \
  --counts PATH/expression_counts.csv --metadata PATH/sample_metadata.csv \
  --run-dir runs/new-design-review --review-pairing \
  --question "Should these samples be paired before differential expression?"
```

This explicit mode returns the computed design report before initializing or calling a model. `scripts/run_design_cases.py` reproduces four controlled cases from the public snapshot: original data, an intentionally mismatched sample ID, reordered metadata and deliberately unbalanced pairing. The original and row-reordered cases request researcher confirmation; the mismatched ID blocks; the unbalanced case requests design review. These are deterministic controls, not four independent autonomous-agent successes. No biological confirmation was supplied for the actual dataset.

Machine-readable recorded results are committed in `output_examples/design_cases.json` and exposed by the read-only viewer. Earlier model-driven design clarification remains in `codex_live_03`; the review gate is new integration work. Confirmation records are bound to the dataset fingerprint, factor and contrast. Confirmation still leads only to statistical method review.

## Current submission materials

The current local revision uses the seven-slide `deliverables/nightshift-pitch/RNA_Evidence_Agent_Nightshift_Pitch.pptx` and teacher-paced Nightshift video. They show saved computed reports and a recorded Nightshift explanation, not a fresh live screen capture. Earlier decision media remains historical.

The source bundle contains the agent and verification code; media assets are separate deliverables. No measured time savings, statistical accuracy advantage or general agent reliability score is claimed.

## Submission media

- [Nightshift decision walkthrough](deliverables/nightshift-demo-teaching/RNA_Evidence_Agent_Nightshift_Demo_Teaching.mp4)
- [Nightshift pitch deck](deliverables/nightshift-pitch/RNA_Evidence_Agent_Nightshift_Pitch.pptx)

The video is a narrated playback of computed reports and an earlier recorded model response. It is not a screen recording or a fresh live model execution. The six slide renders are included beside the deck.


## Nightshift integration

The CLI now defaults to `--backend nightshift`. The adapter uses the official
OpenAI-compatible provider contract, a 180-second timeout, authenticated model
discovery, and `meterless-app: rna-evidence-agent` / `meterless-scope: user` headers.
It does not fall back to another provider. Configure `METERLESS_BASE_URL`
(default `http://127.0.0.1:8088/v1`), `METERLESS_RUNTIME_TOKEN`, and optionally
`METERLESS_MODEL` (default `meterless/auto`) securely in your environment.
Never paste or commit the token. The runtime creates it in its state directory's
`proxy-token` file. Remote endpoints require HTTPS.

Use the existing live command with `--backend nightshift` instead of
`--backend codex`. The response's reported model, requested routing mode,
request/response hashes, and usage are retained in the evidence manifest.
A reported model identifier is provider metadata, not independent attestation.

**Current verification boundary:** the bounded design-explanation feature completed
with local Qwen 2.5 3B and a retained provider receipt. Full code-execution-loop
attempts fail with Nightshift's system-prompt ordering error. Earlier short
responses from smaller models contained inaccuracies or invalid actions and are
not treated as analysis evidence. Empty execution requests are rejected.
The recorded examples do not establish general reliability or prize eligibility.

Provider contract: https://github.com/Meterless/Meterless/blob/main/docs/agent-ready/add-meterless-provider.md

### Bounded Nightshift explanation mode

`--review-pairing --explain-review` computes the design checks first, then asks
Nightshift to explain them. Set `METERLESS_TOKEN_FILE` to the runtime's existing
local token file, or provide `METERLESS_RUNTIME_TOKEN` securely in the environment.
The token is never written to run artifacts. `METERLESS_MODEL=meterless/local`
requests local processing. The resulting `nightshift_explanation.json` records
the reported model, provider receipt, usage and hashes. Its prose is explicitly
unreviewed and cannot override the deterministic decision or authorize analysis.
Without `--explain-review`, design review remains entirely deterministic.

The active runtime routed a short request to Qwen 2.5 3B. Full analysis-loop
requests still fail with the provider's system-prompt ordering error. Changing
the adapter to a single user message did not resolve that error. No successful
full Nightshift-driven code-execution loop is claimed. Existing Codex examples
remain historical examples rather than evidence of Nightshift execution.


### Recorded Nightshift feature result

`runs/nightshift_design_01` completed the bounded design-explanation workflow
with Qwen 2.5 3B through the local Nightshift provider. Its receipt reports
local-only processing. The saved response preserves the need for researcher
confirmation and does not claim a treatment effect. The public example
`output_examples/nightshift_design_01.json` includes the response and receipt.
The viewer renders it separately from historical Codex runs. Provider-reported
consensus and scores are not independent scientific validation; multiple lanes
in this receipt use the same model. No measured reliability or cost advantage
is claimed. Full agent-loop failures remain documented. These additions require a separate upload to update the submitted entry.


Reproduce the bounded feature on your own authorized runtime:

```sh
export METERLESS_TOKEN_FILE="PATH/TO/YOUR/runtime-token"
export METERLESS_MODEL=meterless/local
python run_live.py --review-pairing --explain-review \
  --baseline PATH/TO/rnaseq-agent \
  --counts PATH/expression_counts.csv --metadata PATH/sample_metadata.csv \
  --run-dir runs/new-nightshift-design \
  --question "Explain why pairing needs researcher confirmation."
```

Keep Nightshift open with a local model active. The baseline argument is retained
for CLI compatibility; deterministic design review plus explanation does not
load the baseline agent loop. Use a fresh output directory for each run.
