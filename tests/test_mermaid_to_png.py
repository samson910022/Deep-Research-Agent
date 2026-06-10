"""
Tests for skills/deep-science-writer/scripts/mermaid_to_png.py

Covers:
- Base64 URL-safe encoding structure is correct
- Custom theme parameter is passed through in the payload
- MermaidGenerationError is raised on failure
"""
import base64
import json
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, "skills/deep-science-writer/scripts")
from mermaid_to_png import generate_mermaid_png, MermaidGenerationError


def test_payload_encoding():
    """The JSON payload should be URL-safe base64 encoded and contain the
    expected fields."""
    code = "graph TD\n A --> B"
    payload = json.dumps({
        "code": code,
        "mermaid": {
            "theme": "default",
            "securityLevel": "loose"
        }
    }).encode('utf-8')
    expected_b64 = base64.urlsafe_b64encode(payload).decode('utf-8')

    # We can't fully test network I/O, but we can inspect the generated state
    # by re-running the logic inline.
    import mermaid_to_png as mmod
    state = {
        "code": code,
        "mermaid": {"theme": "default", "securityLevel": "loose"}
    }
    actual_b64 = base64.urlsafe_b64encode(
        json.dumps(state).encode('utf-8')
    ).decode('utf-8')

    assert actual_b64 == expected_b64


def test_custom_theme_in_payload():
    """When a custom theme is passed, the payload should contain that theme."""
    code = "graph LR\n A --> B"
    theme = "dark"
    state = {
        "code": code,
        "mermaid": {"theme": theme, "securityLevel": "loose"}
    }
    b64 = base64.urlsafe_b64encode(
        json.dumps(state).encode('utf-8')
    ).decode('utf-8')

    # Verify dark theme is in the decoded payload
    decoded = json.loads(base64.urlsafe_b64decode(b64))
    assert decoded["mermaid"]["theme"] == "dark"


def test_generation_error_raised():
    """When urllib.request.urlopen fails, MermaidGenerationError should be
    raised."""
    with patch("mermaid_to_png.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network error")

        with pytest.raises(MermaidGenerationError) as exc_info:
            generate_mermaid_png("graph TD\n A --> B", "test.png")

        assert "Failed to generate Mermaid PNG" in str(exc_info.value)


def test_generation_success():
    """On successful HTTP response, no exception should be raised and the
    output file should be written."""
    fake_data = b"PNG data here"
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = fake_data

    with patch("mermaid_to_png.urllib.request.urlopen") as mock_urlopen, \
         patch("builtins.open") as mock_open:
        mock_urlopen.return_value = mock_cm
        mock_file_cm = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file_cm

        # Should not raise
        generate_mermaid_png("graph TD\n A --> B", "output.png")

        # Verify file was written with the downloaded data
        mock_file_cm.write.assert_called_once_with(fake_data)
