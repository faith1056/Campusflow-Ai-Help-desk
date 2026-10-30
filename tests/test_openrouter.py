import unittest
from unittest.mock import Mock, patch

from ai.openrouter import (
    get_openrouter_suggestions,
    OpenRouterProviderError,
)


class TestOpenRouterProvider(unittest.TestCase):

    @patch("ai.openrouter.requests.post")
    def test_returns_ai_suggestions(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Check the Wi-Fi settings and restart the laptop."
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = get_openrouter_suggestions(
            "My laptop cannot connect to the campus Wi-Fi."
        )

        self.assertIn("Check the Wi-Fi settings", result)
        mock_post.assert_called_once()

    def test_rejects_empty_description(self):
        with self.assertRaises((ValueError, OpenRouterProviderError)):
            get_openrouter_suggestions("   ")


if __name__ == "__main__":
    unittest.main()