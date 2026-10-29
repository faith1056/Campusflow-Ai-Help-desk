from ai.groq import get_groq_suggestions, GroqProviderError


description = "My laptop cannot connect to the campus Wi-Fi."

try:
    suggestions = get_groq_suggestions(description)

    print("\nGroq suggestions:")
    print(suggestions)

except GroqProviderError as error:
    print(f"\nGroq error: {error}")