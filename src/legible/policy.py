"""Deciding which pages need OCR, as pure functions.

The whole judgement of this library lives here, and none of it touches a file.
That is deliberate: these rules are the part that is hard to get right and
expensive to get wrong, and rules that can only be exercised against a real
corpus do not get exercised.
"""

from dataclasses import dataclass
from typing import Final

from legible.models import DocumentKind, PageInspection, PageKind

TEXT_CHARACTERS_THRESHOLD: Final[int] = 50
"""Below this many extractable characters, a page is a picture of text.

Measured rather than guessed: a scanned page yields a handful of characters at
most — stray marks the text layer picked up, or a digital stamp applied after
scanning. A born-digital page of prose yields hundreds. Fifty sits in the empty
space between the two, and a header-only cover page is the only thing that
lands near it.
"""


@dataclass(frozen=True, slots=True)
class Policy:
    """The thresholds a caller may disagree with.

    Supplied rather than hardcoded, because the right threshold depends on the
    corpus: engineering drawings carry almost no text and are not scanned,
    while a poor scan with an aggressive text layer can carry more than fifty
    characters of noise.
    """

    text_characters_threshold: int = TEXT_CHARACTERS_THRESHOLD
    skip_blank_pages: bool = True


def classify_page(inspection: PageInspection, policy: Policy) -> PageKind:
    """Whether a page carries its own text, or only a picture of it."""
    if inspection.characters >= policy.text_characters_threshold:
        return PageKind.BORN_DIGITAL
    return PageKind.SCANNED


def needs_ocr(inspection: PageInspection, policy: Policy) -> bool:
    """Whether reading this page with OCR would tell a caller anything new.

    A blank page is not scanned, and OCR would spend a second per page
    discovering that. On a corpus with separator sheets between documents, that
    is the difference between an overnight run and a weekend one.
    """
    if policy.skip_blank_pages and inspection.is_blank:
        return False
    return classify_page(inspection, policy) is PageKind.SCANNED


def classify_document(inspections: tuple[PageInspection, ...], policy: Policy) -> DocumentKind:
    """What a document is made of, once every page has been looked at.

    `MIXED` is the case worth naming. A scanned appendix bound onto a
    born-digital report is common, and treating the whole document as one or
    the other either wastes OCR on text that is already there or silently drops
    the appendix.
    """
    if not inspections:
        return DocumentKind.EMPTY

    kinds = {classify_page(page, policy) for page in inspections}
    if kinds == {PageKind.BORN_DIGITAL}:
        return DocumentKind.BORN_DIGITAL
    if kinds == {PageKind.SCANNED}:
        return DocumentKind.SCANNED
    return DocumentKind.MIXED
