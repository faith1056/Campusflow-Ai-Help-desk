import json
import os
from pathlib import Path

try:
    import psycopg
except ImportError:  # psycopg is only needed when DATABASE_URL is set
    psycopg = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TICKETS_FILE = PROJECT_ROOT / "tickets.json"

_table_ready = False


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

def _database_url():
    """Return the Postgres URL if one is configured, otherwise None."""
    url = os.getenv("DATABASE_URL", "").strip()
    return url or None


def _connect(url):
    if psycopg is None:
        raise OSError(
            "DATABASE_URL is set but the psycopg package is not installed."
        )

    try:
        return psycopg.connect(url, connect_timeout=15)
    except psycopg.Error as error:
        raise OSError("Could not connect to the database.") from error


def _ensure_table(connection):
    global _table_ready

    if _table_ready:
        return

    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                ai_provider TEXT NOT NULL,
                ai_suggestions TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    connection.commit()
    _table_ready = True


def _row_to_ticket(row):
    number, title, description, ai_provider, ai_suggestions = row

    return {
        "id": f"T{number:03d}",
        "title": title,
        "description": description,
        "ai_provider": ai_provider,
        "ai_suggestions": ai_suggestions,
    }


# ---------------------------------------------------------------------------
# JSON file storage (local development and tests)
# ---------------------------------------------------------------------------

def _load_tickets_from_file():
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


def _save_ticket_to_file(title, description, ai_provider, ai_suggestions):
    tickets = _load_tickets_from_file()

    ticket = {
        "id": generate_ticket_id(tickets),
        "title": title,
        "description": description,
        "ai_provider": ai_provider,
        "ai_suggestions": ai_suggestions,
    }

    tickets.append(ticket)

    with TICKETS_FILE.open("w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4)

    return ticket


# ---------------------------------------------------------------------------
# Postgres storage (production)
# ---------------------------------------------------------------------------

def _load_tickets_from_database(url):
    connection = _connect(url)

    try:
        _ensure_table(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, description, ai_provider, ai_suggestions
                FROM tickets
                ORDER BY id
                """
            )
            rows = cursor.fetchall()

        return [_row_to_ticket(row) for row in rows]

    except psycopg.Error as error:
        raise OSError("Could not load tickets from the database.") from error

    finally:
        connection.close()


def _save_ticket_to_database(
    url, title, description, ai_provider, ai_suggestions
):
    connection = _connect(url)

    try:
        _ensure_table(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tickets
                    (title, description, ai_provider, ai_suggestions)
                VALUES (%s, %s, %s, %s)
                RETURNING id, title, description, ai_provider, ai_suggestions
                """,
                (title, description, ai_provider, ai_suggestions),
            )
            row = cursor.fetchone()

        connection.commit()
        return _row_to_ticket(row)

    except psycopg.Error as error:
        raise OSError("Could not save the ticket to the database.") from error

    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Public functions (same names and behavior as before)
# ---------------------------------------------------------------------------

def load_tickets():
    """Load all tickets from Postgres, or from tickets.json locally."""

    url = _database_url()

    if url:
        return _load_tickets_from_database(url)

    return _load_tickets_from_file()


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

    title = title.strip()
    description = description.strip()
    ai_provider = ai_provider.strip()
    ai_suggestions = ai_suggestions.strip()

    url = _database_url()

    if url:
        return _save_ticket_to_database(
            url, title, description, ai_provider, ai_suggestions
        )

    return _save_ticket_to_file(
        title, description, ai_provider, ai_suggestions
    )