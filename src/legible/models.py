"""The records this library passes between its layers.

Dataclasses rather than dictionaries, because every one of these crosses a
module boundary and a `dict[str, Any]` at a boundary is a missing type: callers
guess at keys, typos survive until runtime, and a field that changes shape
changes it silently.
"""

from dataclasses import dataclass
from enum import StrEnum


class PageKind(StrEnum):
    """Whether a page carries its own text, or only a picture of it."""

    BORN_DIGITAL = "born_digital"
    SCANNED = "scanned"


class DocumentKind(StrEnum):
    """What a document is made of, once every page has been looked at."""

    BORN_DIGITAL = "born_digital"
    SCANNED = "scanned"
    MIXED = "mixed"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class PageInspection:
    """What one page contains, before any decision is made about it."""

    number: int
    characters: int
    image_count: int
    table_count: int
    rotation: int

    @property
    def is_blank(self) -> bool:
        """Whether the page holds nothing at all.

        A page with no text, no images and no tables is not scanned — it is
        empty, and OCR would spend a second per page to discover that.
        """
        return self.characters == 0 and self.image_count == 0 and self.table_count == 0


@dataclass(frozen=True, slots=True)
class DocumentInspection:
    """Every page of one document, and what they add up to."""

    pages: tuple[PageInspection, ...]
    kind: DocumentKind

    @property
    def total_characters(self) -> int:
        return sum(page.characters for page in self.pages)


@dataclass(frozen=True, slots=True)
class OcrPage:
    """The result of reading one page with OCR."""

    number: int
    text: str
    confidence: float
    rotation_applied: int

    @property
    def is_confident(self) -> bool:
        """Whether the engine was sure enough of this page to trust it."""
        return self.confidence >= MINIMUM_TRUSTWORTHY_CONFIDENCE


MINIMUM_TRUSTWORTHY_CONFIDENCE: float = 60.0
