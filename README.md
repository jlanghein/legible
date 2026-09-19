# legible

Decide which PDF pages need OCR, and OCR them well when they do.

```python
from legible import PyMuPdfReader, TesseractEngine, OcrSettings, read_document

result = read_document(
    "corpus/manual.pdf",
    PyMuPdfReader(),
    TesseractEngine(),
    settings=OcrSettings(languages=("deu", "eng", "dan")),
)

print(result.inspection.kind)  # DocumentKind.MIXED
print(result.pages_read)  # 3 — the scanned appendix only
for page in result.doubtful_pages:
    print(f"page {page.number} read at {page.confidence}% — review")
```

## Why this exists

A corpus of scanned documents is never all scanned. Reports arrive born-digital with a
scanned appendix bound on; a drawing carries no text and was never scanned at all; a
separator sheet is blank. Running OCR over everything wastes about a second per page and
overwrites text that was already there. Running it over nothing loses the appendix.

Four problems sit between "I have PDFs" and "I have text", and none of them is obvious
until it has cost you a weekend.

### Deciding what is scanned

A page with a handful of extractable characters is a picture of text. A page with
hundreds is prose. The gap between them is wide and mostly empty, so a character
threshold separates them reliably — but the right threshold depends on the corpus, so it
is a field on a `Policy` you supply rather than a number baked into the library.

Blank pages are skipped by default. On a corpus with separator sheets, that alone is the
difference between an overnight run and a weekend one.

### Documents are mixed more often than they are not

`DocumentKind.MIXED` is the case worth naming. Treating a mixed document as born-digital
drops the appendix; treating it as scanned re-reads text that was already perfect.

### Orientation detection is confidently wrong on sparse pages

Tesseract reports a rotation estimate alongside an orientation confidence. On a title
sheet or a drawing it will report nonsense at a very low score, and rotating on that
turns a readable page upside down — worse than leaving it alone. Rotation is applied only
above a threshold you set.

### A confidence number is only useful if it means something

Tesseract returns a row per detected box, including empty ones scored `-1`. Averaging
those in drags a clean page's score toward zero and makes the number useless for deciding
whether to trust a reading. Confidence here is averaged over words that actually carry
text, and `doubtful_pages` surfaces the rest rather than dropping them — a doubtful page
is still better than no page, and silently discarding it loses content nobody knows is
gone.

## Design

```
errors ──► models ──► policy ──┐
          settings ──► backends ──► pipeline
```

`policy` holds every decision and touches no file, so the rules that are hard to get
right are exercised without a corpus. `backends` holds every third-party call behind a
`Protocol`, with the real adapters checked against those Protocols in
`tests/test_backends.py` — a fake is complete by construction and will never notice a
library moving a function elsewhere.

Three runtime dependencies: `pymupdf`, `pytesseract`, `pillow`.

## Install

```bash
uv add legible
```

Tesseract itself must be on `PATH`, with language data for the languages you request.

## Errors

| Error | Meaning |
|---|---|
| `DocumentUnreadableError` | Corrupt, truncated, encrypted or not a document. Retrying will not help |
| `PageRenderError` | One page would not rasterise; the rest of the document may be fine |
| `OcrUnavailableError` | Tesseract is missing or refused. Every page will fail the same way — stop |

All inherit `LegibleError`.

## Development

```bash
uv sync --extra dev
uv run --extra dev ruff format .
uv run --extra dev ruff check --fix .
uv run --extra dev ty check src
uv run --extra dev pytest
```

Run the tools through `uv run`, not `uvx` — `uvx` pins nothing and resolves the newest
release on every invocation, so the checks can change behaviour with nothing in the
repository changing.

See [`AGENTS.md`](AGENTS.md) for the conventions CI enforces.

## Licence

MIT
