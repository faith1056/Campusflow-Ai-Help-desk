import unittest
from unittest.mock import Mock, patch

from ai.ai_manager import get_suggestions


class TestAIManager(unittest.TestCase):

    def test_selects_groq_provider(self):
        mock_groq = Mock(
            return_value="Three troubleshooting suggestions."
        )

        with patch.dict(
            "ai.ai_manager.PROVIDERS",
            {"groq": mock_groq},
        ):
            result = get_suggestions(
                "groq",
                "My laptop cannot connect to Wi-Fi.",
            )

        self.assertEqual(
            result,
            "Three troubleshooting suggestions.",
        )

        mock_groq.assert_called_once_with(
            "My laptop cannot connect to Wi-Fi."
        )

    def test_rejects_unknown_provider(self):
        with self.assertRaises(ValueError):
            get_suggestions(
                "unknown",
                "My laptop cannot connect to Wi-Fi.",
            )

    def test_rejects_empty_description(self):
        with self.assertRaises(ValueError):
            get_suggestions("groq", "   ")


if __name__ == "__main__":
    unittest.main()