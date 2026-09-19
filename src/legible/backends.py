"""What this library needs from PyMuPDF and Tesseract, and the real wiring.

Declared as Protocols so the pipeline can be exercised without either library
installed, and implemented once here so there is a single place that knows the
shape of each third-party call.

That separation earns its keep the moment a dependency moves a function: a fake
is complete by construction and will never notice, so `tests/test_backends.py`
asserts the real adapters against the same Protocols.
"""

from dataclasses import dataclass
from typing import Final, Protocol, TypedDict, runtime_checkable

import pymupdf
import pytesseract
from PIL import Image

from legible.errors import DocumentUnreadableError, OcrUnavailableError, PageRenderError
from legible.models import PageInspection
from legible.settings import OcrSettings

EMPTY_BOX_CONFIDENCE: Final[float] = 0.0
"""At or below this score, Tesseract is reporting a box it found no text in.

`image_to_data` returns one row per detected box and scores the empty ones -1,
so a clean page produces many of them. They are excluded rather than averaged
in, because including them drags a well-read page toward zero and makes the
confidence useless for the only thing it is for.
"""


class TesseractWordData(TypedDict):
    """The two columns of `image_to_data` output this library reads.

    Named rather than passed as a bare mapping: the shape is pytesseract's, not
    ours, and a dictionary crossing a module boundary is a missing type.

    `conf` is `int | str` because pytesseract has returned both across versions,
    and a caller reading the declared type should not be surprised by either.
    """

    conf: list[int | str]
    text: list[str]


@dataclass(frozen=True, slots=True)
class RenderedPage:
    """One page rasterised, ready for OCR."""

    width: int
    height: int
    samples: bytes


@dataclass(frozen=True, slots=True)
class OcrReading:
    """What the OCR engine made of one rendered page."""

    text: str
    mean_confidence: float
    detected_rotation: int
    orientation_confidence: float


@runtime_checkable
class DocumentReader(Protocol):
    """Opening a document and looking at its pages."""

    def inspect(self, path: str) -> tuple[PageInspection, ...]: ...
    def render(self, path: str, page_number: int, scale: float) -> RenderedPage: ...


@runtime_checkable
class OcrEngine(Protocol):
    """Reading a rendered page."""

    def read(self, page: RenderedPage, settings: OcrSettings) -> OcrReading: ...


class PyMuPdfReader:
    """`DocumentReader` backed by PyMuPDF.

    Both the open and the render call catch `Exception` and re-raise it as a
    library error. That is broader than this codebase otherwise allows, and
    deliberate: PyMuPDF surfaces a corrupt file, an empty file, a
    password-protected one and a non-PDF through several unrelated types, and
    enumerating them would leave the one it adds next release uncaught — which
    is the case that matters, because a corpus of thousands of scanned files
    contains every kind of broken there is.

    The translation is the point of this class. Nothing above it imports a
    PyMuPDF exception type.
    """

    def inspect(self, path: str) -> tuple[PageInspection, ...]:
        try:
            document = pymupdf.open(path)
        except Exception as exc:
            message = f"{path!r} could not be opened as a document"
            raise DocumentUnreadableError(message) from exc

        try:
            return tuple(
                self._inspect_page(document[number], number)
                for number in range(document.page_count)
            )
        finally:
            document.close()

    @staticmethod
    def _inspect_page(page: pymupdf.Page, number: int) -> PageInspection:
        return PageInspection(
            number=number,
            characters=len(page.get_text()),
            image_count=len(page.get_images(full=True)),
            table_count=len(page.find_tables().tables),
            rotation=page.rotation,
        )

    def render(self, path: str, page_number: int, scale: float) -> RenderedPage:
        try:
            document = pymupdf.open(path)
        except Exception as exc:
            message = f"{path!r} could not be opened as a document"
            raise DocumentUnreadableError(message) from exc

        try:
            pixmap = document[page_number].get_pixmap(matrix=pymupdf.Matrix(scale, scale))
        except Exception as exc:
            message = f"page {page_number} of {path!r} would not render"
            raise PageRenderError(message) from exc
        else:
            return RenderedPage(width=pixmap.width, height=pixmap.height, samples=pixmap.samples)
        finally:
            document.close()


class TesseractEngine:
    """`OcrEngine` backed by Tesseract, through pytesseract and Pillow."""

    def read(self, page: RenderedPage, settings: OcrSettings) -> OcrReading:
        image = Image.frombytes("RGB", (page.width, page.height), page.samples)

        detected_rotation = 0
        orientation_confidence = 0.0
        if settings.auto_rotate:
            try:
                osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
            except pytesseract.TesseractNotFoundError as exc:
                message = "Tesseract is not installed or not on PATH"
                raise OcrUnavailableError(message) from exc
            except pytesseract.TesseractError:
                detected_rotation = 0
            else:
                detected_rotation = osd.get("rotate", 0)
                orientation_confidence = osd.get("orientation_conf", 0.0)

        if detected_rotation and orientation_confidence > settings.orientation_confidence_threshold:
            image = image.rotate(-detected_rotation, expand=True)
        else:
            detected_rotation = 0

        try:
            data = pytesseract.image_to_data(
                image, lang=settings.language_spec, output_type=pytesseract.Output.DICT
            )
            text = pytesseract.image_to_string(image, lang=settings.language_spec)
        except pytesseract.TesseractNotFoundError as exc:
            message = "Tesseract is not installed or not on PATH"
            raise OcrUnavailableError(message) from exc
        except pytesseract.TesseractError as exc:
            message = f"Tesseract refused the page: {exc}"
            raise OcrUnavailableError(message) from exc

        return OcrReading(
            text=text,
            mean_confidence=_mean_word_confidence(data),
            detected_rotation=detected_rotation,
            orientation_confidence=orientation_confidence,
        )


def _mean_word_confidence(data: TesseractWordData) -> float:
    """The average confidence over words that actually carry text.

    Tesseract reports a row per detected box, including empty ones scored -1.
    Averaging those in drags a clean page's score down toward zero and makes
    the number useless for deciding whether to trust the reading.
    """
    scores = [
        float(confidence)
        for confidence, text in zip(data["conf"], data["text"], strict=True)
        if text.strip() and float(confidence) > EMPTY_BOX_CONFIDENCE
    ]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 1)
