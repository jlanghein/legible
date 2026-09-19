import pytest

from legible.models import DocumentKind, PageInspection, PageKind
from legible.policy import Policy, classify_document, classify_page, needs_ocr

DEFAULT = Policy()


def page(**overrides) -> PageInspection:
    values = {"number": 0, "characters": 0, "image_count": 0, "table_count": 0, "rotation": 0}
    return PageInspection(**{**values, **overrides})


def test_a_page_of_prose_carries_its_own_text():
    assert classify_page(page(characters=2400), DEFAULT) is PageKind.BORN_DIGITAL


def test_a_page_with_only_scanner_noise_is_scanned():
    assert classify_page(page(characters=7, image_count=1), DEFAULT) is PageKind.SCANNED


def test_the_threshold_is_inclusive():
    assert classify_page(page(characters=50), DEFAULT) is PageKind.BORN_DIGITAL
    assert classify_page(page(characters=49), DEFAULT) is PageKind.SCANNED


def test_a_caller_may_raise_the_threshold_for_a_noisy_corpus():
    noisy = Policy(text_characters_threshold=200)
    assert classify_page(page(characters=120), noisy) is PageKind.SCANNED
    assert classify_page(page(characters=120), DEFAULT) is PageKind.BORN_DIGITAL


def test_a_scanned_page_needs_ocr():
    assert needs_ocr(page(characters=3, image_count=1), DEFAULT)


def test_a_born_digital_page_does_not():
    assert not needs_ocr(page(characters=2400), DEFAULT)


def test_a_blank_page_is_not_worth_ocr():
    assert page().is_blank
    assert not needs_ocr(page(), DEFAULT)


def test_a_caller_may_insist_on_ocr_for_blank_pages():
    assert needs_ocr(page(), Policy(skip_blank_pages=False))


def test_a_page_holding_only_a_table_is_not_blank():
    assert not page(table_count=1).is_blank


@pytest.mark.parametrize(
    ("pages", "expected"),
    [
        ((), DocumentKind.EMPTY),
        ((2400,), DocumentKind.BORN_DIGITAL),
        ((2400, 1800), DocumentKind.BORN_DIGITAL),
        ((4,), DocumentKind.SCANNED),
        ((4, 0), DocumentKind.SCANNED),
        ((2400, 4), DocumentKind.MIXED),
    ],
)
def test_a_document_is_what_its_pages_add_up_to(pages: tuple[int, ...], expected: DocumentKind):
    inspections = tuple(page(number=i, characters=c) for i, c in enumerate(pages))
    assert classify_document(inspections, DEFAULT) is expected


def test_a_scanned_appendix_makes_the_document_mixed():
    report = tuple(page(number=i, characters=2400) for i in range(10))
    appendix = tuple(page(number=10 + i, characters=6, image_count=1) for i in range(3))
    assert classify_document(report + appendix, DEFAULT) is DocumentKind.MIXED
