import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from storage.tickets import save_ticket, load_tickets, generate_ticket_id


class TestTicketStorage(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.tickets_file = Path(self.temp_directory.name) / "tickets.json"

        self.file_patcher = patch(
            "storage.tickets.TICKETS_FILE",
            self.tickets_file,
        )
        self.file_patcher.start()

    def tearDown(self):
        self.file_patcher.stop()
        self.temp_directory.cleanup()

    def test_saves_ticket_with_correct_information(self):
        ticket = save_ticket(
            "Wi-Fi problem",
            "Cannot connect to campus Wi-Fi.",
            "groq",
            "Check the Wi-Fi settings.",
        )

        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["title"], "Wi-Fi problem")
        self.assertEqual(ticket["ai_provider"], "groq")

        saved_tickets = load_tickets()
        self.assertEqual(len(saved_tickets), 1)
        self.assertEqual(saved_tickets[0]["id"], "T001")

    def test_generates_sequential_ticket_ids(self):
        existing_tickets = [
            {"id": "T001"},
            {"id": "T002"},
            {"id": "T007"},
        ]

        self.assertEqual(
            generate_ticket_id(existing_tickets),
            "T008",
        )

    def test_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            save_ticket(
                "   ",
                "Cannot connect to campus Wi-Fi.",
                "groq",
                "Check the Wi-Fi settings.",
            )

    def test_rejects_empty_description(self):
        with self.assertRaises(ValueError):
            save_ticket(
                "Wi-Fi problem",
                "   ",
                "groq",
                "Check the Wi-Fi settings.",
            )

    def test_preserves_existing_tickets(self):
        save_ticket(
            "First ticket",
            "First description",
            "groq",
            "First suggestion",
        )

        save_ticket(
            "Second ticket",
            "Second description",
            "gemini",
            "Second suggestion",
        )

        tickets = load_tickets()

        self.assertEqual(len(tickets), 2)
        self.assertEqual(tickets[0]["id"], "T001")
        self.assertEqual(tickets[1]["id"], "T002")


if __name__ == "__main__":
    unittest.main()
