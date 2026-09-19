"""Decide which PDF pages need OCR, and OCR them well when they do."""

from legible.backends import (
    DocumentReader,
    OcrEngine,
    OcrReading,
    PyMuPdfReader,
    RenderedPage,
    TesseractEngine,
)
from legible.errors import (
    DocumentUnreadableError,
    LegibleError,
    OcrUnavailableError,
    PageRenderError,
)
from legible.models import DocumentInspection, DocumentKind, OcrPage, PageInspection, PageKind
from legible.pipeline import ReadDocument, inspect_document, read_document
from legible.policy import Policy, classify_document, classify_page, needs_ocr
from legible.settings import OcrSettings

__all__ = [
    "DocumentInspection",
    "DocumentKind",
    "DocumentReader",
    "DocumentUnreadableError",
    "LegibleError",
    "OcrEngine",
    "OcrPage",
    "OcrReading",
    "OcrSettings",
    "OcrUnavailableError",
    "PageInspection",
    "PageKind",
    "PageRenderError",
    "Policy",
    "PyMuPdfReader",
    "ReadDocument",
    "RenderedPage",
    "TesseractEngine",
    "classify_document",
    "classify_page",
    "inspect_document",
    "needs_ocr",
    "read_document",
]
