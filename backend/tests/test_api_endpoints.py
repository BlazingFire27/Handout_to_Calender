import os
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from io import BytesIO

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from api import app

client = TestClient(app)

@patch("api.process_pdf")
def test_valid_pdf_extraction(mock_process_pdf):
    """TC1: Submit a valid PDF, expect HTTP 200 and JSON."""
    # Mock the LLM backend response so we don't need .env API keys
    mock_process_pdf.return_value = (
        "Mocked Course", 
        [{"event": "Quiz 1", "date": "10/10/2026"}], 
        [{"topic": "Intro"}], 
        [{"book": "Mock Book"}]
    )

    pdf_file = BytesIO(b"%PDF-1.4 mock content")
    pdf_file.name = "syllabus.pdf"

    response = client.post(
        "/generate",
        files={"file": ("syllabus.pdf", pdf_file, "application/pdf")},
        data={"date_format": "DMY"}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["course_title"] == "Mocked Course"
    assert len(json_data["evaluation_scheme"]) == 1
    mock_process_pdf.assert_called_once()

def test_invalid_file_type():
    """TC2: Submit an invalid file type, expect HTTP 400."""
    txt_file = BytesIO(b"Just some text")
    txt_file.name = "syllabus.txt"

    response = client.post(
        "/generate",
        files={"file": ("syllabus.txt", txt_file, "text/plain")},
        data={"date_format": "DMY"}
    )

    assert response.status_code == 400
    assert "File must be a PDF" in response.json()["error"]

def test_missing_file_payload():
    """TC3: Missing file payload, expect HTTP 422."""
    response = client.post(
        "/generate",
        data={"date_format": "DMY"}
    )
    
    assert response.status_code == 422 # FastAPI validation error

@patch.dict(os.environ, {"ENVIRONMENT": "production"})
def test_rate_limiting():
    """TC4: Rate limit hit (21 requests), expect HTTP 429."""
    # Send 20 successful requests (they need a file to bypass FastAPI's 422 validation)
    for _ in range(20):
        dummy_file = BytesIO(b"%PDF-1.4 mock")
        dummy_file.name = "dummy.pdf"
        res = client.post(
            "/generate", 
            files={"file": ("dummy.pdf", dummy_file, "application/pdf")},
            data={"date_format": "DMY"}
        )
        # Mocked LLM isn't patched here, so it might fail with 500, but it WILL hit the rate limiter
        # To be safe, we just care that it doesn't return 429 yet
        assert res.status_code != 429

    # 21st request should be rate limited
    dummy_file = BytesIO(b"%PDF-1.4 mock")
    dummy_file.name = "dummy.pdf"
    response = client.post(
        "/generate", 
        files={"file": ("dummy.pdf", dummy_file, "application/pdf")},
        data={"date_format": "DMY"}
    )
    assert response.status_code == 429

@patch("api.process_pdf")
def test_default_date_format(mock_process_pdf):
    """TC5: Submit without date_format, expect fallback to DMY."""
    mock_process_pdf.return_value = ("Mocked Course", [], [], [])

    pdf_file = BytesIO(b"%PDF-1.4 mock content")
    pdf_file.name = "syllabus2.pdf"

    # Notice we do not pass `data={"date_format": ...}`
    response = client.post(
        "/generate",
        files={"file": ("syllabus2.pdf", pdf_file, "application/pdf")}
    )

    assert response.status_code == 200
    # Verify process_pdf was called with the default 'DMY'
    args, kwargs = mock_process_pdf.call_args
    assert kwargs.get("user_date_format") == "DMY"
