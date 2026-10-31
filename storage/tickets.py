import json
import os
from pathlib import Path

try:
    import psycopg
except ImportError:  # psycopg is only needed when DATABASE_URL is set
    psycopg = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TICKETS_FILE = PROJECT_ROOT / "tickets.json"

VALID_STATUSES = ("Open", "In progress", "Resolved")
DEFAULT_STATUS = "Open"

_table_ready = False


class TicketNotFoundError(Exception):
    """Raised when a ticket ID does not exist."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _database_url():
    """Return the Postgres URL if one is configured, otherwise None."""
    url = os.getenv("DATABASE_URL", "").strip()
    return url or None


def normalize_status(status):
    """Return the canonical status name, or raise ValueError."""
    if isinstance(status, str):
        for valid_status in VALID_STATUSES:
            if status.strip().lower() == valid_status.lower():
                return valid_status

    raise ValueError(
        "Status must be one of: " + ", ".join(VALID_STATUSES) + "."
    )


def _ticket_number(ticket_id):
    """Convert 'T003' into 3, or raise TicketNotFoundError."""
    if (
        isinstance(ticket_id, str)
        and ticket_id.startswith("T")
        and ticket_id[1:].isdigit()
    ):
        return int(ticket_id[1:])

    raise TicketNotFoundError("Ticket not found.")


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
        # Adds the status column to tables created before this feature
        cursor.execute(
            """
            ALTER TABLE tickets
            ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'Open'
            """
        )
    connection.commit()
    _table_ready = True


def _row_to_ticket(row):
    number, title, description, ai_provider, ai_suggestions, status = row

    return {
        "id": f"T{number:03d}",
        "title": title,
        "description": description,
        "ai_provider": ai_provider,
        "ai_suggestions": ai_suggestions,
        "status": status,
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


def _write_tickets_to_file(tickets):
    with TICKETS_FILE.open("w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4)


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
        "status": DEFAULT_STATUS,
    }

    tickets.append(ticket)
    _write_tickets_to_file(tickets)

    return ticket


def _update_status_in_file(ticket_id, status):
    tickets = _load_tickets_from_file()

    for ticket in tickets:
        if isinstance(ticket, dict) and ticket.get("id") == ticket_id:
            ticket["status"] = status
            _write_tickets_to_file(tickets)
            return ticket

    raise TicketNotFoundError("Ticket not found.")


# ---------------------------------------------------------------------------
# Postgres storage (production)
# ---------------------------------------------------------------------------

_COLUMNS = "id, title, description, ai_provider, ai_suggestions, status"


def _load_tickets_from_database(url):
    connection = _connect(url)

    try:
        _ensure_table(connection)

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT {_COLUMNS} FROM tickets ORDER BY id")
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
                f"""
                INSERT INTO tickets
                    (title, description, ai_provider, ai_suggestions, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING {_COLUMNS}
                """,
                (
                    title,
                    description,
                    ai_provider,
                    ai_suggestions,
                    DEFAULT_STATUS,
                ),
            )
            row = cursor.fetchone()

        connection.commit()
        return _row_to_ticket(row)

    except psycopg.Error as error:
        raise OSError("Could not save the ticket to the database.") from error

    finally:
        connection.close()


def _update_status_in_database(url, ticket_id, status):
    number = _ticket_number(ticket_id)
    connection = _connect(url)

    try:
        _ensure_table(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE tickets
                SET status = %s
                WHERE id = %s
                RETURNING {_COLUMNS}
                """,
                (status, number),
            )
            row = cursor.fetchone()

        connection.commit()

        if row is None:
            raise TicketNotFoundError("Ticket not found.")

        return _row_to_ticket(row)

    except psycopg.Error as error:
        raise OSError("Could not update the ticket.") from error

    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Public functions
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


def update_ticket_status(ticket_id, status):
    """Change a ticket's status and return the updated ticket."""

    status = normalize_status(status)

    url = _database_url()

    if url:
        return _update_status_in_database(url, ticket_id, status)

    return _update_status_in_file(ticket_id, status)