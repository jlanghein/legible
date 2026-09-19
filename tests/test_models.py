from legible.models import DocumentInspection, DocumentKind, OcrPage, PageInspection


def page(**overrides) -> PageInspection:
    values = {"number": 0, "characters": 0, "image_count": 0, "table_count": 0, "rotation": 0}
    return PageInspection(**{**values, **overrides})


def test_total_characters_sums_the_pages():
    doc = DocumentInspection(
        pages=(page(characters=100), page(characters=250)), kind=DocumentKind.BORN_DIGITAL
    )
    assert doc.total_characters == 350


def test_an_empty_document_has_no_characters():
    assert DocumentInspection(pages=(), kind=DocumentKind.EMPTY).total_characters == 0


def test_a_page_with_an_image_is_not_blank():
    assert not page(image_count=1).is_blank


def test_a_confident_ocr_page_is_trusted():
    assert OcrPage(number=0, text="x", confidence=88.4, rotation_applied=0).is_confident


def test_a_doubtful_ocr_page_is_not():
    assert not OcrPage(number=0, text="x", confidence=31.2, rotation_applied=0).is_confident
