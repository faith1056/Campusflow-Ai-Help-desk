import hmac
import os

from flask import Flask, Response, render_template, request, jsonify

from ai.ai_manager import get_suggestions, AIManagerError
from storage.tickets import load_tickets, save_ticket


app = Flask(__name__)


@app.before_request
def require_login():
    # Skip auth in tests and when no password is configured (local dev)
    if app.config.get("TESTING"):
        return None

    password = os.getenv("APP_PASSWORD")
    if not password:
        return None

    # Let Render's HEAD / port check through
    if request.method == "HEAD" and request.path == "/":
        return None

    username = os.getenv("APP_USERNAME", "admin")
    auth = request.authorization

    if (
        auth
        and hmac.compare_digest((auth.username or "").encode(), username.encode())
        and hmac.compare_digest((auth.password or "").encode(), password.encode())
    ):
        return None

    return Response(
        "Login required",
        401,
        {"WWW-Authenticate": 'Basic realm="CampusFlow"'},
    )


@app.route("/api/provider-status", methods=["GET"])
def provider_status():
    from ai.gemini import GEMINI_API_KEY
    from ai.groq import GROQ_API_KEY
    from ai.openrouter import OPENROUTER_API_KEY

    providers = {
        "Gemini": bool(GEMINI_API_KEY),
        "Groq": bool(GROQ_API_KEY),
        "OpenRouter": bool(OPENROUTER_API_KEY),
    }

    configured = sum(providers.values())

    return jsonify({
        "configured": configured,
        "total": len(providers),
        "providers": providers,
    })


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/tickets", methods=["GET"])
def get_tickets():
    try:
        tickets = load_tickets()
        return jsonify({"tickets": tickets}), 200

    except (ValueError, OSError):
        app.logger.exception("Failed to load tickets")
        return jsonify({
            "error": "Unable to load tickets."
        }), 500


@app.route("/api/diagnose", methods=["POST"])
def diagnose_ticket():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request must contain valid JSON."
        }), 400

    title = data.get("title")
    description = data.get("description")
    provider = data.get("provider", "gemini")

    if not isinstance(title, str) or not title.strip():
        return jsonify({
            "error": "Ticket title cannot be empty."
        }), 400

    if not isinstance(description, str) or not description.strip():
        return jsonify({
            "error": "Ticket description cannot be empty."
        }), 400

    try:
        suggestions = get_suggestions(provider, description)

        ticket = save_ticket(
            title,
            description,
            provider,
            suggestions,
        )

        return jsonify({
            "message": "Ticket diagnosed successfully.",
            "ticket": ticket,
            "suggestions": suggestions,
        }), 201

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except AIManagerError:
        app.logger.exception("AI diagnosis failed")
        return jsonify({
            "error": "The selected AI provider could not process this ticket."
        }), 502

    except OSError:
        app.logger.exception("Failed to save ticket")
        return jsonify({
            "error": "AI suggestions were generated, but the ticket could not be saved."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)