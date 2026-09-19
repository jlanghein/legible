"""In-memory stand-ins for the PDF reader and the OCR engine."""

from dataclasses import dataclass, field

from legible.backends import OcrReading, RenderedPage
from legible.errors import DocumentUnreadableError
from legible.models import PageInspection
from legible.settings import OcrSettings


@dataclass
class FakeReader:
    """Serves prepared inspections and records what was rendered."""

    pages: tuple[PageInspection, ...] = ()
    unreadable: bool = False
    rendered: list[int] = field(default_factory=list)

    def inspect(self, path: str) -> tuple[PageInspection, ...]:
        if self.unreadable:
            message = f"{path!r} could not be opened as a document"
            raise DocumentUnreadableError(message)
        return self.pages

    def render(self, path: str, page_number: int, scale: float) -> RenderedPage:
        self.rendered.append(page_number)
        return RenderedPage(width=1, height=1, samples=b"\x00\x00\x00")


@dataclass
class FakeEngine:
    """Returns a fixed reading and counts how often it was asked."""

    text: str = "read text"
    confidence: float = 91.5
    detected_rotation: int = 0
    calls: int = 0

    def read(self, page: RenderedPage, settings: OcrSettings) -> OcrReading:
        self.calls += 1
        return OcrReading(
            text=self.text,
            mean_confidence=self.confidence,
            detected_rotation=self.detected_rotation,
            orientation_confidence=0.0,
        )
