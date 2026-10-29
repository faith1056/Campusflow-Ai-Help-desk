import os
import requests

from dotenv import load_dotenv


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-3.5-flash-lite"

URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent"
)


class GeminiProviderError(Exception):
    """Raised when Gemini cannot provide suggestions."""


def get_gemini_suggestions(description):
    """Generate troubleshooting suggestions using Gemini."""

    if not GEMINI_API_KEY:
        raise GeminiProviderError(
            "Gemini API key is missing. Check your .env file."
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
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        suggestions = data["candidates"][0]["content"]["parts"][0]["text"]

        if not suggestions.strip():
            raise GeminiProviderError(
                "Gemini returned an empty response."
            )

        return suggestions

    except requests.exceptions.Timeout as error:
        raise GeminiProviderError(
            "Gemini request timed out."
        ) from error

    except requests.exceptions.HTTPError as error:
        status = (
            error.response.status_code
            if error.response is not None
            else None
        )

        if status == 400:
            message = "Gemini rejected the request. Check its settings."

        elif status in (401, 403):
            message = "Gemini authentication failed. Check your API key."

        elif status == 404:
            message = "The Gemini model or endpoint was not found."

        elif status == 429:
            message = "Gemini's API usage limit may have been reached."

        else:
            message = f"Gemini returned an HTTP error: {status}."

        raise GeminiProviderError(message) from error

    except requests.exceptions.RequestException as error:
        raise GeminiProviderError(
            "Could not connect to Gemini. Check your internet connection."
        ) from error

    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise GeminiProviderError(
            "Gemini returned an unexpected response."
        ) from error