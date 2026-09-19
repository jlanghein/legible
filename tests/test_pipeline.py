import pytest

from legible.errors import DocumentUnreadableError
from legible.models import DocumentKind, PageInspection
from legible.pipeline import inspect_document, read_document
from legible.policy import Policy
from tests.fakes import FakeEngine, FakeReader

PATH = "corpus/manual.pdf"


def page(number: int, characters: int, **overrides) -> PageInspection:
    values = {"image_count": 0, "table_count": 0, "rotation": 0}
    return PageInspection(number=number, characters=characters, **{**values, **overrides})


def test_a_born_digital_document_is_never_sent_to_ocr():
    reader = FakeReader(pages=(page(0, 2400), page(1, 1800)))
    engine = FakeEngine()

    result = read_document(PATH, reader, engine)

    assert engine.calls == 0
    assert result.pages_read == 0
    assert result.inspection.kind is DocumentKind.BORN_DIGITAL


def test_only_the_scanned_pages_of_a_mixed_document_are_read():
    reader = FakeReader(pages=(page(0, 2400), page(1, 4, image_count=1), page(2, 1800)))
    engine = FakeEngine()

    result = read_document(PATH, reader, engine)

    assert engine.calls == 1
    assert reader.rendered == [1]
    assert result.ocr_pages[0].number == 1
    assert result.inspection.kind is DocumentKind.MIXED


def test_blank_pages_are_not_rendered():
    reader = FakeReader(pages=(page(0, 0), page(1, 3, image_count=1)))
    engine = FakeEngine()

    read_document(PATH, reader, engine)

    assert reader.rendered == [1]


def test_a_caller_may_insist_on_reading_blank_pages():
    reader = FakeReader(pages=(page(0, 0),))
    engine = FakeEngine()

    read_document(PATH, reader, engine, policy=Policy(skip_blank_pages=False))

    assert reader.rendered == [0]


def test_the_render_scale_follows_the_requested_dpi():
    from legible.settings import OcrSettings

    assert OcrSettings(render_dpi=300).render_scale == pytest.approx(300 / 72)
    assert OcrSettings(render_dpi=150).render_scale == pytest.approx(150 / 72)


def test_languages_are_joined_the_way_tesseract_wants_them():
    from legible.settings import OcrSettings

    assert OcrSettings(languages=("deu", "eng", "dan")).language_spec == "deu+eng+dan"


def test_doubtful_pages_are_surfaced_rather_than_dropped():
    reader = FakeReader(pages=(page(0, 2, image_count=1),))
    engine = FakeEngine(confidence=22.0)

    result = read_document(PATH, reader, engine)

    assert result.pages_read == 1
    assert len(result.doubtful_pages) == 1
    assert result.ocr_pages[0].text == "read text"


def test_a_confident_reading_is_not_flagged():
    reader = FakeReader(pages=(page(0, 2, image_count=1),))
    result = read_document(PATH, reader, FakeEngine(confidence=94.0))

    assert result.doubtful_pages == ()


def test_the_applied_rotation_is_carried_through():
    reader = FakeReader(pages=(page(0, 2, image_count=1),))
    result = read_document(PATH, reader, FakeEngine(detected_rotation=90))

    assert result.ocr_pages[0].rotation_applied == 90


def test_an_unreadable_document_is_raised_not_returned_empty():
    with pytest.raises(DocumentUnreadableError):
        read_document(PATH, FakeReader(unreadable=True), FakeEngine())


def test_inspecting_does_not_read_anything():
    reader = FakeReader(pages=(page(0, 3, image_count=1),))
    engine = FakeEngine()

    inspect_document(PATH, reader, Policy())

    assert engine.calls == 0
    assert reader.rendered == []


def test_an_empty_document_is_reported_as_such():
    result = read_document(PATH, FakeReader(pages=()), FakeEngine())
    assert result.inspection.kind is DocumentKind.EMPTY
