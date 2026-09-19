# Rotation and confidence

## Orientation detection is confidently wrong on sparse pages

Tesseract's OSD reports a rotation estimate *and* an orientation confidence. On a page
with plenty of text the estimate is reliable. On a title sheet, a drawing, or a page with
a dozen words, it will report a confident-looking rotation at a very low score.

Acting on that turns a readable page upside down, which is strictly worse than leaving it
alone — an unrotated page still OCRs poorly but recognisably, while a wrongly rotated one
produces nothing usable.

```python
from legible import OcrSettings

OcrSettings(orientation_confidence_threshold=2.0)  # default
OcrSettings(auto_rotate=False)  # never rotate
```

`OcrPage.rotation_applied` records what was actually done and reports `0` when the
estimate was rejected — so a caller reviewing output can tell "not rotated" from "rotated
by zero".

## Confidence has to exclude the empty boxes

`image_to_data` returns one row per detected box, and boxes with no text are scored `-1`.
A clean page produces many of them.

Averaging naively means a perfectly read page scores near zero, and the number stops
being usable for the only thing it is for: deciding whether to trust the reading.

`legible` averages over rows carrying non-empty text with a positive score. A page
reading at 91% is one you can use; one at 22% is not.

## Doubtful pages are surfaced, not dropped

```python
result = read_document(path, reader, engine)

for page in result.doubtful_pages:
    print(f"page {page.number}: {page.confidence}% — review")
```

`MINIMUM_TRUSTWORTHY_CONFIDENCE` is 60. Below that, `OcrPage.is_confident` is `False` and
the page appears in `doubtful_pages`.

It still appears in `ocr_pages` with its text intact. That is deliberate: a doubtful page
is usually better than no page, and filtering it silently loses content nobody knows is
missing. Flagging it lets a human decide.

## DPI

```python
OcrSettings(render_dpi=300)  # default
```

300 is Tesseract's documented sweet spot for scanned text. Below roughly 200, accuracy
falls away; above 400, each page takes materially longer to render and read for no
measurable gain.

The render scale derives from it — `dpi / 72`, because 72 user-space units per inch is
fixed by the PDF specification. That is a constant of the format, not a tuning knob,
which is why it is not on `OcrSettings`.
