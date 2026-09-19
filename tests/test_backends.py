"""The real adapters must satisfy the Protocols the pipeline depends on.

A fake is complete by construction, so it can never catch a third-party library
moving a function into another namespace or changing a signature. These checks
can, and they are the reason the adapters exist as a separate layer at all.
"""

from legible.backends import DocumentReader, OcrEngine, PyMuPdfReader, TesseractEngine
from tests.fakes import FakeEngine, FakeReader


def test_the_real_reader_satisfies_the_protocol():
    assert isinstance(PyMuPdfReader(), DocumentReader)


def test_the_real_engine_satisfies_the_protocol():
    assert isinstance(TesseractEngine(), OcrEngine)


def test_the_fakes_satisfy_the_same_protocols():
    assert isinstance(FakeReader(), DocumentReader)
    assert isinstance(FakeEngine(), OcrEngine)


def test_every_protocol_method_resolves_on_the_real_reader():
    reader = PyMuPdfReader()
    for name in DocumentReader.__protocol_attrs__:
        assert callable(getattr(reader, name)), f"{name} is not callable on PyMuPdfReader"


def test_every_protocol_method_resolves_on_the_real_engine():
    engine = TesseractEngine()
    for name in OcrEngine.__protocol_attrs__:
        assert callable(getattr(engine, name)), f"{name} is not callable on TesseractEngine"
