import re
import textwrap

from colorama import Fore, Style, init
from ai.ai_manager import get_suggestions, AIManagerError
from storage.tickets import save_ticket


# ---------- TERMINAL SETTINGS ----------

init(autoreset=True)

WIDTH = 70
CONTENT_WIDTH = WIDTH - 2


# ---------- HEADER AND DISPLAY FUNCTIONS ----------

def print_header():
    title = "CAMPUSFLOW"
    subtitle = "AI-POWERED IT SUPPORT"

    print()
    print(Fore.CYAN + Style.BRIGHT + "╔" + "═" * (WIDTH - 2) + "╗")
    print(Fore.CYAN + Style.BRIGHT + "║" + title.center(WIDTH - 2) + "║")
    print(Fore.CYAN + "║" + subtitle.center(WIDTH - 2) + "║")
    print(Fore.CYAN + Style.BRIGHT + "╚" + "═" * (WIDTH - 2) + "╝")


def print_section(title, color=Fore.CYAN):
    print()
    print(color + Style.BRIGHT + "┌" + "─" * (WIDTH - 2) + "┐")
    print(color + Style.BRIGHT + "│" + title.center(WIDTH - 2) + "│")
    print(color + Style.BRIGHT + "├" + "─" * (WIDTH - 2) + "┤")


def print_box_line(text="", color=Fore.WHITE, indent=2):
    available_width = CONTENT_WIDTH - indent

    lines = textwrap.wrap(
        str(text),
        width=available_width,
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]

    for line in lines:
        content = (" " * indent + line).ljust(CONTENT_WIDTH)
        print(color + "│" + content + "│")


def print_box_bottom(color=Fore.CYAN):
    print(color + "└" + "─" * (WIDTH - 2) + "┘")


def print_ticket_field(label, value):
    """Display ticket details with aligned labels."""

    label_width = 15
    value_width = CONTENT_WIDTH - label_width - 4

    lines = textwrap.wrap(
        str(value),
        width=value_width,
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]

    for index, line in enumerate(lines):
        if index == 0:
            content = f"  {label:<{label_width}}{line}"
        else:
            content = f"  {'':<{label_width}}{line}"

        print(
            Fore.WHITE
            + "│"
            + content.ljust(CONTENT_WIDTH)
            + "│"
        )


# ---------- AI RESPONSE FORMATTING ----------

def clean_ai_text(text):
    """Remove common Markdown formatting from AI responses."""

    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "", text)

    return text.strip()


def print_ai_suggestions(text):
    """Display AI suggestions inside the CampusFlow layout."""

    for line in text.splitlines():
        line = clean_ai_text(line)

        if not line:
            print_box_line()
        else:
            print_box_line(line, Fore.WHITE, indent=2)


# ---------- PROVIDER MENU ----------

def choose_provider():
    """Ask the user to select an AI provider."""

    providers = {
        "1": "gemini",
        "2": "groq",
        "3": "openrouter",
    }

    print_section("SELECT AI PROVIDER")

    print_box_line("1. Gemini", Fore.YELLOW)
    print_box_line("2. Groq", Fore.YELLOW)
    print_box_line("3. OpenRouter", Fore.YELLOW)

    print_box_bottom()

    choice = input(
        Fore.CYAN + "\nChoose a provider (1-3): "
    ).strip()

    if choice not in providers:
        print(
            Fore.RED
            + "\nInvalid selection. Please choose 1, 2, or 3."
        )
        return None

    return providers[choice]


# ---------- TICKET DETAILS ----------

def get_ticket_details():
    """Collect and validate the ticket title and description."""

    print_section("CREATE SUPPORT TICKET")
    print_box_line("Enter a short title for your IT problem.")
    print_box_bottom()

    title = input(
        Fore.CYAN + "\nTicket title: "
    ).strip()

    if not title:
        print(Fore.RED + "\nTicket title cannot be empty.")
        return None

    print_section("PROBLEM DESCRIPTION")
    print_box_line("Describe the IT problem you are experiencing.")
    print_box_bottom()

    description = input(
        Fore.CYAN + "\nDescribe the problem: "
    ).strip()

    if not description:
        print(Fore.RED + "\nProblem description cannot be empty.")
        return None

    return title, description


# ---------- AI PROCESSING AND TICKET STORAGE ----------

def display_suggestions(provider, title, description):
    """Generate AI suggestions, save the ticket, and display results."""

    provider_names = {
        "gemini": "Gemini",
        "groq": "Groq",
        "openrouter": "OpenRouter",
    }

    print_section("TROUBLESHOOTING SUGGESTIONS")

    print_ticket_field("Ticket title:", title)
    print_ticket_field("Description:", description)

    print_box_line(
        f"Selected provider: {provider_names[provider]}",
        Fore.YELLOW,
    )

    print_box_line("Generating suggestions...", Fore.CYAN)
    print_box_bottom()

    try:
        # Request troubleshooting suggestions from the selected AI.
        suggestions = get_suggestions(provider, description)

        # Confirm that the AI request has finished.
        print(
            Fore.GREEN
            + Style.BRIGHT
            + "\nAI response received successfully!"
        )

    except AIManagerError as error:
        print_section("AI SERVICE ERROR", Fore.RED)
        print_box_line(str(error), Fore.RED)
        print_box_bottom(Fore.RED)
        return

    except Exception:
        print_section("UNEXPECTED ERROR", Fore.RED)
        print_box_line(
            "Something unexpected happened while requesting "
            "AI suggestions.",
            Fore.RED,
        )
        print_box_bottom(Fore.RED)
        return

    # Save the ticket and its AI response.
    try:
        ticket = save_ticket(
            title,
            description,
            provider,
            suggestions,
        )

    except (ValueError, OSError) as error:
        print_section("TICKET STORAGE ERROR", Fore.RED)
        print_box_line(str(error), Fore.RED)
        print_box_bottom(Fore.RED)

        # Still show the AI response even if saving fails.
        print_section("AI RESPONSE", Fore.GREEN)
        print_ai_suggestions(suggestions)
        print_box_bottom(Fore.GREEN)
        return

    # Confirm that the ticket was saved.
    print_section("TICKET SAVED", Fore.GREEN)
    print_ticket_field("Ticket ID:", ticket["id"])
    print_ticket_field("Ticket title:", ticket["title"])
    print_ticket_field("AI provider:", ticket["ai_provider"])
    print_box_bottom(Fore.GREEN)

    # Display the actual AI response.
    print_section("AI RESPONSE", Fore.GREEN)
    print_ai_suggestions(suggestions)
    print_box_bottom(Fore.GREEN)


# ---------- MAIN PROGRAM ----------

def main():
    print_header()

    provider = choose_provider()

    if provider is None:
        return

    ticket_details = get_ticket_details()

    if ticket_details is None:
        return

    title, description = ticket_details

    display_suggestions(provider, title, description)

    print()
    print(
        Fore.CYAN
        + Style.BRIGHT
        + "Thank you for using CampusFlow AI Support!"
    )


if __name__ == "__main__":
    main()