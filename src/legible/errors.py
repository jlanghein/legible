"""The errors a caller has to handle.

Three, and deliberately few. A caller wants to distinguish "this file is not a
document I can read", "this page would not render" and "Tesseract is not
installed or would not run" — and nothing finer. Everything the underlying
libraries raise is translated into one of these, so no caller has to import
`pymupdf` or `pytesseract` exception types to write a correct `except` clause.
"""


class LegibleError(Exception):
    """Base for everything this library raises."""


class DocumentUnreadableError(LegibleError):
    """Raised when a file cannot be opened as a document.

    Corrupt, truncated, password-protected or simply not a PDF. All four are
    the same thing to a caller: this file yields no pages and retrying will not
    change that.
    """


class PageRenderError(LegibleError):
    """Raised when a page cannot be rasterised for OCR.

    Distinct from an unreadable document: the rest of the document may render
    perfectly, so a caller can record the page and continue.
    """


class OcrUnavailableError(LegibleError):
    """Raised when the OCR engine is missing or refused to run.

    Not a property of the document. Every page will fail the same way until
    somebody installs Tesseract or fixes its language data, so a caller should
    stop rather than work through the corpus failing once per page.
    """
