import unittest
from unittest.mock import patch

from app import app


class TestCampusFlowApp(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_dashboard_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CampusFlow", response.data)

    def test_provider_status_returns_json(self):
        response = self.client.get("/api/provider-status")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIn("providers", data)
        self.assertIn("configured", data)
        self.assertIn("total", data)

    @patch("app.load_tickets", return_value=[])
    def test_ticket_list_returns_json(self, mock_load_tickets):
        response = self.client.get("/api/tickets")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"tickets": []})
        mock_load_tickets.assert_called_once()

    def test_diagnose_rejects_missing_title(self):
        response = self.client.post(
            "/api/diagnose",
            json={
                "title": "",
                "description": "Campus Wi-Fi is not working.",
                "provider": "groq",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_diagnose_rejects_missing_description(self):
        response = self.client.post(
            "/api/diagnose",
            json={
                "title": "Wi-Fi problem",
                "description": "",
                "provider": "groq",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    @patch("app.get_suggestions")
    def test_diagnose_rejects_unknown_provider(self, mock_get_suggestions):
        response = self.client.post(
            "/api/diagnose",
            json={
                "title": "Wi-Fi problem",
                "description": "Campus Wi-Fi is not working.",
                "provider": "unknown",
            },
        )

        self.assertEqual(response.status_code, 400)
        mock_get_suggestions.assert_not_called()


if __name__ == "__main__":
    unittest.main()
