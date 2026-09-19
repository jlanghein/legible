"""What the OCR engine is told, as a record the caller supplies.

None of these are properties of this library: the right DPI depends on the
scanner, the right languages on the corpus, and the rotation threshold on how
much a caller trusts orientation detection. Hardcoding them would make the
library right for exactly one corpus.
"""

from dataclasses import dataclass
from typing import Final

PDF_POINTS_PER_INCH: Final[int] = 72
"""PDF user-space units per inch, fixed by the PDF specification.

The render matrix is a scale factor, so a target DPI becomes `dpi / 72`. This
is a constant of the format, not a tuning knob, which is why it is not on
`OcrSettings`.
"""

DEFAULT_RENDER_DPI: Final[int] = 300
"""Tesseract's documented sweet spot for scanned text.

Below roughly 200 accuracy falls away; above 400 the page takes materially
longer to render and to read for no measurable gain.
"""

DEFAULT_ORIENTATION_CONFIDENCE: Final[float] = 2.0
"""Below this, orientation detection is guessing.

Tesseract reports an orientation confidence alongside its rotation estimate,
and on a sparse page — a title sheet, a drawing — it will confidently report
nonsense at a very low score. Rotating on that turns a readable page upside
down, which is worse than leaving it alone.
"""


@dataclass(frozen=True, slots=True)
class OcrSettings:
    """How to render and read a page."""

    languages: tuple[str, ...] = ("eng",)
    render_dpi: int = DEFAULT_RENDER_DPI
    orientation_confidence_threshold: float = DEFAULT_ORIENTATION_CONFIDENCE
    auto_rotate: bool = True

    @property
    def language_spec(self) -> str:
        """The languages as Tesseract wants them: `deu+eng+dan`."""
        return "+".join(self.languages)

    @property
    def render_scale(self) -> float:
        """The render matrix scale factor for the requested DPI."""
        return self.render_dpi / PDF_POINTS_PER_INCH
