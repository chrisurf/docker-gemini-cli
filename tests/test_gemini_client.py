import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from gemini_client import GeminiClient


@pytest.fixture
def mock_gemini_client():
    with patch("google.generativeai.configure"), patch(
        "google.generativeai.GenerativeModel"
    ):
        client = GeminiClient()
        return client


@pytest.mark.asyncio
async def test_health_check_success(mock_gemini_client):
    with patch.object(mock_gemini_client, "generate_response") as mock_generate:
        mock_generate.return_value = {"success": True}
        result = await mock_gemini_client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_failure(mock_gemini_client):
    with patch.object(mock_gemini_client, "generate_response") as mock_generate:
        mock_generate.side_effect = Exception("API Error")
        result = await mock_gemini_client.health_check()
        assert result is False


def test_prepare_prompt(mock_gemini_client):
    prompt = "Test task"
    context = {"key": "value"}
    result = mock_gemini_client._prepare_prompt(prompt, context)
    assert "Test task" in result
    assert "key: value" in result
