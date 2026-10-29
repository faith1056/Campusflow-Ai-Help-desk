from ai.openrouter import (
    get_openrouter_suggestions,
    OpenRouterProviderError,
)


description = "My laptop cannot connect to the campus Wi-Fi."

try:
    suggestions = get_openrouter_suggestions(description)

    print("\nOpenRouter suggestions:")
    print(suggestions)

except OpenRouterProviderError as error:
    print(f"\nOpenRouter error: {error}")