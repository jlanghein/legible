# Getting Started

## Install

```bash
uv add legible
```

Python 3.13 or later. **Tesseract must be on `PATH`**, with language data installed for
each language you request — `legible` shells out to it and cannot supply it.

```bash
brew install tesseract tesseract-lang        # macOS
apt install tesseract-ocr tesseract-ocr-deu  # Debian/Ubuntu
```

## Inspect without reading

Looking at a document costs almost nothing. Reading it costs about a second per page.

```python
from legible import PyMuPdfReader, Policy, inspect_document

inspection = inspect_document("corpus/manual.pdf", PyMuPdfReader(), Policy())

print(inspection.kind)  # DocumentKind.MIXED
print(len(inspection.pages))  # 42
print(inspection.total_characters)  # 31_204
```

Useful on its own: run it across a corpus first to find out how much of it is actually
scanned before committing to an OCR run.

## Read what needs reading

```python
from legible import OcrSettings, PyMuPdfReader, TesseractEngine, read_document

result = read_document(
    "corpus/manual.pdf",
    PyMuPdfReader(),
    TesseractEngine(),
    settings=OcrSettings(languages=("deu", "eng", "dan")),
)
```

Born-digital pages are never rendered. Blank pages are skipped.

## Tune the policy

```python
from legible import Policy

Policy(text_characters_threshold=200)  # noisy scans with an aggressive text layer
Policy(skip_blank_pages=False)  # read everything, whatever it looks like
```

!!! tip "When to raise the threshold"
    A poor scan can pick up more than fifty characters of noise in its text layer and be
    classified born-digital. If a corpus produces documents that look born-digital but
    contain gibberish, raise the threshold rather than disabling the check.

!!! tip "When to lower it"
    Engineering drawings and plan sets carry almost no text and were never scanned.
    Lowering the threshold stops the library rendering them for nothing.

## Tune the OCR

```python
from legible import OcrSettings

OcrSettings(
    languages=("deu", "eng"),
    render_dpi=300,
    orientation_confidence_threshold=2.0,
    auto_rotate=True,
)
```

## Handle the three errors

```python
from legible import DocumentUnreadableError, OcrUnavailableError, PageRenderError

try:
    result = read_document(path, reader, engine)
except DocumentUnreadableError:
    ...  # record and move to the next file
except PageRenderError:
    ...  # one page; the document may still be worth keeping
except OcrUnavailableError:
    raise  # every page will fail the same way — stop the run
```

`OcrUnavailableError` is the one to treat differently. It is not a property of the
document, so working through a corpus failing once per page wastes hours discovering the
same missing binary.

## Test without PDFs

Both backends are `Protocol`s, so a fake is enough:

```python
from legible import read_document
from legible.models import PageInspection


class FakeReader:
    def inspect(self, path):
        return (PageInspection(0, 4, 1, 0, 0),)

    def render(self, path, page_number, scale): ...
```
