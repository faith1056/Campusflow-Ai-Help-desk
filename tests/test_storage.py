import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from storage.tickets import (
    TicketNotFoundError,
    generate_ticket_id,
    load_tickets,
    save_ticket,
    update_ticket_status,
)


class TestTicketStorage(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.tickets_file = Path(self.temp_directory.name) / "tickets.json"

        self.file_patcher = patch(
            "storage.tickets.TICKETS_FILE",
            self.tickets_file,
        )
        self.file_patcher.start()

        # Always use the JSON file in tests, never the real database
        self.env_patcher = patch.dict(os.environ)
        self.env_patcher.start()
        os.environ.pop("DATABASE_URL", None)

    def tearDown(self):
        self.env_patcher.stop()
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

    def test_new_tickets_start_as_open(self):
        ticket = save_ticket(
            "Wi-Fi problem",
            "Cannot connect to campus Wi-Fi.",
            "groq",
            "Check the Wi-Fi settings.",
        )

        self.assertEqual(ticket["status"], "Open")

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

    def test_updates_ticket_status(self):
        save_ticket("First", "First description", "groq", "Suggestion")
        save_ticket("Second", "Second description", "gemini", "Suggestion")

        updated = update_ticket_status("T002", "In progress")

        self.assertEqual(updated["status"], "In progress")

        tickets = load_tickets()
        self.assertEqual(tickets[0]["status"], "Open")
        self.assertEqual(tickets[1]["status"], "In progress")

    def test_status_is_case_insensitive(self):
        save_ticket("First", "First description", "groq", "Suggestion")

        updated = update_ticket_status("T001", "resolved")

        self.assertEqual(updated["status"], "Resolved")

    def test_rejects_invalid_status(self):
        save_ticket("First", "First description", "groq", "Suggestion")

        with self.assertRaises(ValueError):
            update_ticket_status("T001", "Done")

    def test_unknown_ticket_raises_not_found(self):
        with self.assertRaises(TicketNotFoundError):
            update_ticket_status("T999", "Resolved")


if __name__ == "__main__":
    unittest.main()