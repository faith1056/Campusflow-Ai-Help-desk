from ai.gemini import (
    get_gemini_suggestions,
    GeminiProviderError,
)

description = "My laptop cannot connect to the campus Wi-Fi."

try:
    suggestions = get_gemini_suggestions(description)

    print("\nGemini suggestions:")
    print(suggestions)

except GeminiProviderError as error:
    print(f"\nGemini error: {error}")