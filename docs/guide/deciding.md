# Deciding what is scanned

## The signal

A page that carries its own text yields hundreds or thousands of extractable characters.
A page that is a picture of text yields a handful — stray marks the text layer caught, or
a digital stamp applied after scanning.

The gap between those two is wide and mostly empty, which is what makes a character count
a reliable separator rather than a guess.

```python
from legible import Policy, classify_page
from legible.models import PageInspection

page = PageInspection(number=0, characters=7, image_count=1, table_count=0, rotation=0)
classify_page(page, Policy())  # PageKind.SCANNED
```

## Why the threshold is yours

`TEXT_CHARACTERS_THRESHOLD` defaults to 50, documented in the source with its reasoning.
It is still a field on `Policy` rather than a fixed constant, because the right value
depends on what you are reading:

| Corpus | Adjustment |
|---|---|
| Poor scans with aggressive text layers | **Raise it.** Noise can exceed 50 characters |
| Engineering drawings, plan sets | **Lower it.** Almost no text, never scanned |
| Clean modern PDFs | Leave it |

## Blank pages are not scanned pages

```python
page = PageInspection(number=3, characters=0, image_count=0, table_count=0, rotation=0)
page.is_blank  # True
```

A page with no text, no images and no tables holds nothing. OCR would spend a second
discovering that.

On a corpus with separator sheets between documents — common in anything that came out of
a batch scanner — skipping them is the difference between an overnight run and a weekend
one. Set `Policy(skip_blank_pages=False)` if you would rather confirm.

## Mixed is the normal case

```python
from legible import classify_document

classify_document(report_pages + appendix_pages, Policy())  # DocumentKind.MIXED
```

A born-digital report with a scanned appendix bound onto the end is ordinary, not exotic.
Naming the case matters because both ways of ignoring it lose something:

- Treat it as born-digital → the appendix is silently empty
- Treat it as scanned → every page is re-read, and good text is replaced by OCR output

`read_document` uses the per-page decision regardless of document kind, so a mixed
document reads only its scanned pages. `DocumentKind` is for reporting across a corpus,
not for branching.
