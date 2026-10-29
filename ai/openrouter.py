import os
import requests

from dotenv import load_dotenv


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"

URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProviderError(Exception):
    """Raised when OpenRouter cannot provide suggestions."""


def get_openrouter_suggestions(description):
    """Generate troubleshooting suggestions using OpenRouter."""

    if not OPENROUTER_API_KEY:
        raise OpenRouterProviderError(
            "OpenRouter API key is missing. Check your .env file."
        )

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Ticket description cannot be empty.")

    prompt = (
        "You are an IT support assistant. "
        "Analyze the reported problem and suggest exactly 3 "
        "practical ways to investigate or fix it. "
        "Use simple English. Number each suggestion. "
        "Keep each suggestion short. "
        "Do not claim the problem has already been fixed.\n\n"
        f"Ticket description: {description}"
    )

    try:
        response = requests.post(
            URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        suggestions = data["choices"][0]["message"]["content"]

        if not suggestions or not suggestions.strip():
            raise OpenRouterProviderError(
                "OpenRouter returned an empty response."
            )

        return suggestions

    except requests.exceptions.Timeout as error:
        raise OpenRouterProviderError(
            "OpenRouter request timed out."
        ) from error

    except requests.exceptions.HTTPError as error:
        status = (
            error.response.status_code
            if error.response is not None
            else None
        )

        if status in (401, 403):
            message = (
                "OpenRouter authentication failed. Check your API key."
            )

        elif status == 404:
            message = "The OpenRouter model or endpoint was not found."

        elif status == 429:
            message = (
                "OpenRouter's rate limit or usage limit may have been reached."
            )

        elif status == 400:
            message = (
                "OpenRouter rejected the request. Check the model and request."
            )

        else:
            message = f"OpenRouter returned an HTTP error: {status}."

        raise OpenRouterProviderError(message) from error

    except requests.exceptions.RequestException as error:
        raise OpenRouterProviderError(
            "Could not connect to OpenRouter. Check your internet connection."
        ) from error

    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise OpenRouterProviderError(
            "OpenRouter returned an unexpected response."
        ) from error