from ai.gemini import (
    get_gemini_suggestions,
    GeminiProviderError,
)
from ai.groq import (
    get_groq_suggestions,
    GroqProviderError,
)
from ai.openrouter import (
    get_openrouter_suggestions,
    OpenRouterProviderError,
)


PROVIDERS = {
    "gemini": get_gemini_suggestions,
    "groq": get_groq_suggestions,
    "openrouter": get_openrouter_suggestions,
}


class AIManagerError(Exception):
    """Raised when the AI manager cannot provide suggestions."""


def get_suggestions(provider, description):
    """Get suggestions from the provider selected by the user."""

    if not isinstance(provider, str):
        raise ValueError(
            "Provider must be a string."
        )

    provider = provider.strip().lower()

    if provider not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())

        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Choose one of: {available}."
        )

    if not isinstance(description, str) or not description.strip():
        raise ValueError(
            "Ticket description cannot be empty."
        )

    try:
        return PROVIDERS[provider](description)

    except (
        GeminiProviderError,
        GroqProviderError,
        OpenRouterProviderError,
    ) as error:
        raise AIManagerError(
            f"{provider.capitalize()} failed: {error}"
        ) from error