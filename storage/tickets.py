import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TICKETS_FILE = PROJECT_ROOT / "tickets.json"


def load_tickets():
    """Load existing tickets from the JSON file."""

    if not TICKETS_FILE.exists():
        return []

    try:
        with TICKETS_FILE.open("r", encoding="utf-8") as file:
            tickets = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            "The tickets.json file contains invalid JSON."
        ) from error

    if not isinstance(tickets, list):
        raise ValueError(
            "The tickets.json file must contain a list of tickets."
        )

    return tickets


def generate_ticket_id(tickets):
    """Generate the next ticket ID."""

    highest_number = 0

    for ticket in tickets:
        if not isinstance(ticket, dict):
            raise ValueError(
                "The tickets.json file contains an invalid ticket."
            )

        ticket_id = ticket.get("id", "")

        if (
            isinstance(ticket_id, str)
            and ticket_id.startswith("T")
            and ticket_id[1:].isdigit()
        ):
            number = int(ticket_id[1:])
            highest_number = max(highest_number, number)

    return f"T{highest_number + 1:03d}"


def save_ticket(title, description, ai_provider, ai_suggestions):
    """Save a ticket with its AI troubleshooting suggestions."""

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Ticket title cannot be empty.")

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Ticket description cannot be empty.")

    if not isinstance(ai_provider, str) or not ai_provider.strip():
        raise ValueError("AI provider cannot be empty.")

    if not isinstance(ai_suggestions, str) or not ai_suggestions.strip():
        raise ValueError("AI suggestions cannot be empty.")

    tickets = load_tickets()

    ticket = {
        "id": generate_ticket_id(tickets),
        "title": title.strip(),
        "description": description.strip(),
        "ai_provider": ai_provider.strip(),
        "ai_suggestions": ai_suggestions.strip(),
    }

    tickets.append(ticket)

    with TICKETS_FILE.open("w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4)

    return ticket