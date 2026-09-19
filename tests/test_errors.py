import pytest

from legible.errors import (
    DocumentUnreadableError,
    LegibleError,
    OcrUnavailableError,
    PageRenderError,
)


@pytest.mark.parametrize("error", [DocumentUnreadableError, PageRenderError, OcrUnavailableError])
def test_every_error_is_catchable_as_the_base(error: type[LegibleError]):
    message = "boom"
    with pytest.raises(LegibleError):
        raise error(message)
