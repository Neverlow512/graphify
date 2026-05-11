# Smali Extractor — Sandbox

Standalone development sandbox for the graphify smali language extractor. The parser is written implementation-ready — when validated, it copies into `graphify/extract.py` with minimal changes.

See `roadmap.md` for the full validation plan.

______________________________________________________________________

## What it extracts

All constructs are explicit bytecode facts. Every edge carries `EXTRACTED` confidence.

| Construct           | Source                                                            | Relation          |
| ------------------- | ----------------------------------------------------------------- | ----------------- |
| Class               | `.class`                                                          | node              |
| Superclass          | `.super`                                                          | `inherits`        |
| Interface           | `.implements`                                                     | `implements`      |
| Method              | `.method` / `.end method`                                         | node + `contains` |
| Field               | `.field`                                                          | node + `contains` |
| Outer → inner class | `$` in class descriptor                                           | `contains`        |
| Method calls        | `invoke-virtual/direct/static/interface/super/polymorphic/custom` | `calls`           |
| Field reads         | `iget*`, `sget*` (all type variants)                              | `reads`           |
| Field writes        | `iput*`, `sput*` (all type variants)                              | `writes`          |

**Intentionally skipped:** annotation content, exception handlers, debug directives, register declarations, switch tables, array data. These produce no meaningful cross-entity edges and are skipped by every graphify extractor.

______________________________________________________________________

## Output schema

```python
{
    "nodes": [
        {
            "id": str,             # lowercase alphanumeric, e.g. "mainactivity_m_onclick"
            "label": str,          # human-readable, e.g. "com.example.MainActivity.onClick()"
            "file_type": "code",
            "source_file": str,    # absolute path, empty for stub nodes
            "source_location": str # "L{line}", empty for stub nodes
        }
    ],
    "edges": [
        {
            "source": str,
            "target": str,
            "relation": str,       # inherits | implements | contains | calls | reads | writes
            "confidence": "EXTRACTED",
            "source_file": str,
            "source_location": str,
            "weight": 1.0,
            "context": str         # "call" | "read" | "write" — omitted for structural edges
        }
    ],
    "input_tokens": 0,
    "output_tokens": 0
}
```

Stub nodes are created for external references (classes, methods, fields not defined in the current file) to prevent dangling edges. They have empty `source_file` and `source_location`.

______________________________________________________________________

## Node ID format

Method nodes carry an `_m_` namespace to avoid collision with field nodes of the same name. Bracketed names (`<init>`, `<clinit>`, `<test_method>`) carry `_b_` instead.

| Kind             | Example label               | Example ID                  |
| ---------------- | --------------------------- | --------------------------- |
| Class            | `com.example.Foo`           | `com_example_foo`           |
| Field            | `com.example.Foo.count`     | `com_example_foo_count`     |
| Method           | `com.example.Foo.onClick()` | `com_example_foo_m_onclick` |
| Bracketed method | `com.example.Foo.<init>()`  | `com_example_foo_b_init`    |
| Stub (external)  | `java.lang.Object.<init>()` | `java_lang_object_b_init`   |

______________________________________________________________________

## Edge deduplication

Smali edges are deduplicated on `(source, target, relation, source_location)` rather than the simpler `(source, target, relation)` used by other graphify extractors. This is intentional: a single method body can contain multiple distinct calls to the same target (e.g. two `invoke-direct` calls to `<init>` in a `<clinit>` block), each on a different line. Collapsing them would silently drop real bytecode facts. The `source_location` field preserves the distinction while still preventing exact-duplicate lines from being recorded twice.

______________________________________________________________________

## Analyzer

After each parser run, `analyzer/summarize.py` aggregates all per-file results and writes two files into the run directory:

- `summary.json` — machine-readable metrics and flags
- `summary.md` — human-readable table for quick review

**What the analyzer reports:**

| Metric / Flag       | Description                                                             |
| ------------------- | ----------------------------------------------------------------------- |
| `total_files`       | Number of smali files processed                                         |
| `error_files`       | Files where the parser raised an exception                              |
| `total_nodes`       | Aggregate node count across all files                                   |
| `total_edges`       | Aggregate edge count across all files                                   |
| `node_kinds`        | Breakdown by heuristic kind: `class`, `method`, `field`                 |
| `stub_ratio`        | Fraction of nodes that are stubs (external references)                  |
| `high_call_nodes`   | Nodes with unusually high incoming `calls` edge count (> 50)            |
| `id_collisions`     | Node IDs shared by two or more distinct labels — indicates a parser bug |
| `files_with_errors` | List of files that failed, with their error messages                    |

**Known limitation:** the `_node_kind` heuristic classifies PascalCase field names (e.g. `Handler`, `Builder`) as classes because they are indistinguishable from class names by label alone. CONSTANT_CASE (`TAG`, `MAX_SIZE`) and lowercase/special-start names (`count`, `$VALUES`, `<test_field>`) are classified correctly. The node kind breakdown in `summary.json` is approximate for PascalCase members. This cannot be fixed without adding a `kind` field to the node schema.

______________________________________________________________________

## Structure

```
smali-sandbox/
  parser/
    extract_smali.py     # the extractor — implementation-ready
  analyzer/
    summarize.py         # post-run aggregator: writes summary.json + summary.md
    __init__.py
  fixtures/              # hand-crafted .smali files for unit testing
    sample.smali         # full class: all invoke types, field reads/writes
    obfuscated.smali     # opaque package names (La/b/c; pattern)
    inner_classes.smali  # outer→$Inner and outer→$1 anonymous class
    modern_invoke.smali  # invoke-polymorphic, invoke-polymorphic/range, invoke-custom
    field_access.smali   # all iget/iput/sget/sput type variants
  corpus/                # real smali files (Phase 2+)
    jesusfreke/          # JesusFreke reference suite — 128 files (tracked in git)
    apk-sample/          # baksmali output from real APKs (gitignored — reproduce with baksmali)
      antennapod/        # AntennaPod 3.11.2 — pure Java, 7089 files
      tusky/             # Tusky 32.2 — pure Kotlin, 7966 files
      fdroid/            # F-Droid 2.0-alpha8 — Java + Kotlin Compose hybrid, 9231 files
  outputs/               # JSON output from parser runs, auto-categorized (gitignored)
    fixtures/run-NNN/                  # runs against hand-crafted fixtures
    corpus/jesusfreke/run-NNN/         # runs against the JesusFreke reference corpus
    corpus/apk-sample/antennapod/run-NNN/
    corpus/apk-sample/tusky/run-NNN/
    corpus/apk-sample/fdroid/run-NNN/
  tests/
    test_smali.py        # 35 unit tests covering all fixtures and corpus regressions
    test_regex_coverage.py  # 35 parametrized tests, one per regex path
    test_summarize.py    # 18 tests for the analyzer aggregation and flag logic
  run_parser.py          # convenience runner — auto-categorizes output, increments run-NNN
  requirements.txt       # pinned dev dependencies
  roadmap.md             # validation phases and exit conditions
```

______________________________________________________________________

## Commands

| Action                      | Command                                                                       |
| --------------------------- | ----------------------------------------------------------------------------- |
| Install dependencies        | `pip install -r smali-sandbox/requirements.txt`                               |
| Run tests                   | `pytest smali-sandbox/tests/ -v`                                              |
| Lint                        | `ruff check smali-sandbox/`                                                   |
| Type check                  | `mypy smali-sandbox/parser/ smali-sandbox/analyzer/ --ignore-missing-imports` |
| Run parser on fixtures      | `python smali-sandbox/run_parser.py smali-sandbox/fixtures/`                  |
| Run parser on a single file | `python smali-sandbox/run_parser.py path/to/file.smali`                       |
| Run parser on corpus        | `python smali-sandbox/run_parser.py smali-sandbox/corpus/jesusfreke/`         |
| Disassemble an APK          | `baksmali disassemble app.apk -o smali-sandbox/corpus/apk-sample/myapp/`      |
| Run parser on an APK corpus | `python smali-sandbox/run_parser.py smali-sandbox/corpus/apk-sample/myapp/`   |

All commands run from the project root with the venv activated. `baksmali` must be installed globally (`baksmali --version` to confirm).

The runner auto-detects the output category from the input path and mirrors the corpus folder structure: `fixtures/` → `outputs/fixtures/run-NNN/`, `corpus/jesusfreke/` → `outputs/corpus/jesusfreke/run-NNN/`, `corpus/apk-sample/` → `outputs/corpus/apk-sample/run-NNN/`. A new numbered `run-NNN/` subdirectory is created on each execution.

______________________________________________________________________

## Current status

| Phase                         | Status       | Summary                                                                        |
| ----------------------------- | ------------ | ------------------------------------------------------------------------------ |
| 1 — Parser + fixtures         | **Complete** | 97 unit tests pass, ruff and mypy clean                                        |
| 2 — Reference corpus          | **Complete** | 128 files, 7 bugs found and fixed, regression tests added                      |
| 3 — Real APK benchmark        | **Complete** | 24,286 files across 3 apps, zero errors, zero collisions, 100% invoke coverage |
| 4 — Androguard accuracy check | **Complete** | 99.87% match on extractable `calls` edges for AntennaPod (Java)                |
| 5 — Port into graphify        | **Complete** | 15 smali tests pass (262 total), e2e verified on AntennaPod corpus             |

______________________________________________________________________

**Phase 1** — Parser passes ruff, mypy, and 97 unit tests with zero failures.

**Phase 2** — Validated against the JesusFreke reference corpus (128 files). Seven parser bugs found and fixed:

| #   | Bug                                                                             | Fix                                                                           |
| --- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1   | Bracketed method names (`<init>`, `<clinit>`) collided with same-name field IDs | `_make_id` prefixes methods with `_m_`, bracketed names with `_b_`            |
| 2   | `Enum.values()` node missing — array receiver `[LEnum;` not matched             | Regex extended to `(\[+[BCDFIJSZ]\|\[*L[^;]+;)`                               |
| 3   | Multiple `invoke-static` calls to same target collapsed to one edge             | Dedup key extended to include `source_location`                               |
| 4   | Hyphenated method names (`test-method`) dropped by `_METHOD_START_RE`           | Added `-` to method name character class                                      |
| 5   | Primitive array invoke receivers (`[I`, `[B`) not matched                       | `_INVOKE_RE` and `_INVOKE_POLY_RE` unified to cover all primitive array types |
| 6   | Bracketed field names (`<test_field>`) not matched in `iget/iput/sget/sput`     | Field name capture group extended to `[\w$<>\-]+`                             |
| 7   | `varargs` modifier caused entire method block to be skipped                     | Added `varargs` to the modifier alternation in `_METHOD_START_RE`             |

Regression tests added for every bug. The analyzer generates `summary.json` and `summary.md` per run for efficient triage.

**Phase 3** — Validated against three real APKs (24,286 files total, re-run post-varargs fix):

| App                | Language              | Files | Errors | ID collisions | Total nodes | Total edges | invoke coverage |
| ------------------ | --------------------- | ----: | -----: | ------------: | ----------: | ----------: | --------------: |
| AntennaPod 3.11.2  | Pure Java             | 7,089 |      0 |             0 |     193,095 |     349,665 |            100% |
| Tusky 32.2         | Pure Kotlin           | 7,966 |      0 |             0 |     236,354 |     503,787 |            100% |
| F-Droid 2.0-alpha8 | Java + Kotlin Compose | 9,231 |      0 |             0 |     203,200 |     395,020 |            100% |

Silent methods manually verified against smali source — all confirmed as abstract declarations, trivial returns, or bridge synthetics with no `invoke-*` in their bodies. Kotlin-specific patterns (coroutine state machines, companion objects, lambda classes, `$SwitchMap`) parsed correctly.

**Phase 4** — Androguard accuracy check completed for all three APKs:

| App        | Parser edges | Androguard edges | Matched | Only ours | Only Androguard | Accuracy (extractable) |
| ---------- | -----------: | ---------------: | ------: | --------: | --------------: | ---------------------: |
| AntennaPod |      102,126 |          159,110 | 101,993 |       133 |          57,117 |             **99.87%** |
| Tusky      |      142,493 |          143,409 | 134,764 |     7,729 |           8,645 |             **94.58%** |
| F-Droid    |      136,265 |          281,965 | 136,035 |       230 |         145,930 |             **99.83%** |

Interpretation of the gaps:

- **AntennaPod / F-Droid "Only Androguard"** — virtual dispatch resolution across class boundaries. Androguard performs whole-program call graph analysis; our parser operates per-file only. Expected and by design.
- **AntennaPod / F-Droid "Only ours"** — `array.clone()` calls that Androguard intentionally omits.
- **Tusky "Only ours" / "Only Androguard" (~8k each)** — case normalization mismatch in Androguard for heavily obfuscated Kotlin APKs. Androguard normalizes single-letter method names (e.g., `j` → `J`) when resolving Kotlin coroutine dispatch, causing label divergence. The smali source has both `j()` and `J()` as distinct methods; our parser reads them correctly as-is. This is an Androguard artifact, not a parser bug.

Known limitations documented in `roadmap.md`:

- **Overloaded method merging** — parameter signatures are stripped from labels, so overloaded methods share a single node. Approximately 7.95% of method declarations are affected (measured on AntennaPod). This is consistent with `graphify`'s schema and cannot be resolved without adding a `kind` or signature field to the node schema.
- **`_node_kind` heuristic** — the analyzer classifies nodes by label shape. PascalCase labels (e.g., `Handler`, `Builder`) are ambiguous: they are classified as classes but may be fields. CONSTANT_CASE and bracketed names are classified correctly.

**Next:** Phase 5 — Port into graphify.
