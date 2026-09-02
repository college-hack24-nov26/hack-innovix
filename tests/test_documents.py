from app.ocr.mock_provider import MockOCRProvider


def test_mock_ocr():
    text = MockOCRProvider().extract_text("demo.pdf")
    assert "Metformin" in text
