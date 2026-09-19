"""Inspecting a document and reading only the pages that need it.

The orchestration, and nothing else: the decisions live in `policy`, the I/O in
`backends`. Keeping them apart is what lets a caller change the threshold
without touching PyMuPDF, and swap PyMuPDF without touching the threshold.
"""

from dataclasses import dataclass

from legible.backends import DocumentReader, OcrEngine
from legible.models import DocumentInspection, OcrPage
from legible.policy import Policy, classify_document, needs_ocr
from legible.settings import OcrSettings


@dataclass(frozen=True, slots=True)
class ReadDocument:
    """One document, inspected and — where it was needed — read."""

    inspection: DocumentInspection
    ocr_pages: tuple[OcrPage, ...]

    @property
    def pages_read(self) -> int:
        return len(self.ocr_pages)

    @property
    def doubtful_pages(self) -> tuple[OcrPage, ...]:
        """Pages the engine was not confident about.

        Surfaced rather than filtered, because a caller usually wants to keep
        the text and flag it for review — a doubtful page is still better than
        no page, and dropping it silently loses content nobody knows is gone.
        """
        return tuple(page for page in self.ocr_pages if not page.is_confident)


def inspect_document(path: str, reader: DocumentReader, policy: Policy) -> DocumentInspection:
    """Look at every page without reading any of them."""
    pages = reader.inspect(path)
    return DocumentInspection(pages=pages, kind=classify_document(pages, policy))


def read_document(
    path: str,
    reader: DocumentReader,
    engine: OcrEngine,
    *,
    policy: Policy | None = None,
    settings: OcrSettings | None = None,
) -> ReadDocument:
    """Inspect a document, then OCR only the pages that would gain from it.

    A born-digital document is inspected and returned with no OCR at all. On a
    mixed corpus this is most of the saving: rendering and reading a page costs
    about a second, and a text layer that is already there costs nothing.
    """
    active_policy = policy or Policy()
    active_settings = settings or OcrSettings()

    inspection = inspect_document(path, reader, active_policy)
    pages = tuple(
        _read_page(path, page.number, reader, engine, active_settings)
        for page in inspection.pages
        if needs_ocr(page, active_policy)
    )
    return ReadDocument(inspection=inspection, ocr_pages=pages)


def _read_page(
    path: str, number: int, reader: DocumentReader, engine: OcrEngine, settings: OcrSettings
) -> OcrPage:
    rendered = reader.render(path, number, settings.render_scale)
    reading = engine.read(rendered, settings)
    return OcrPage(
        number=number,
        text=reading.text,
        confidence=reading.mean_confidence,
        rotation_applied=reading.detected_rotation,
    )
