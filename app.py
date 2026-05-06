"""
Helena — Rude Friend Chatbot
Flask application with routes and session logic.
"""

from flask import Flask, render_template, request, jsonify
from gemini import get_reply

app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory session store
# { "uuid": [ {role, parts}, ... ] }
# ---------------------------------------------------------------------------
sessions = {}
MAX_HISTORY = 10


def get_history(session_id):
    """Return the conversation history for a given session."""
    return sessions.get(session_id, [])


def update_history(session_id, user_msg, model_reply):
    """Append the latest exchange and trim to MAX_HISTORY entries."""
    history = sessions.setdefault(session_id, [])
    history.append({"role": "user",  "parts": [{"text": user_msg}]})
    history.append({"role": "model", "parts": [{"text": model_reply}]})
    sessions[session_id] = history[-MAX_HISTORY:]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page UI."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Process a user message and return Helena's reply.
    Expects JSON: { "session_id": str, "message": str }
    Returns JSON:  { "reply": str }
    """
    data = request.get_json(silent=True)

    if not data or "session_id" not in data or "message" not in data:
        return jsonify({"error": "Missing session_id or message"}), 400

    session_id = data["session_id"]
    user_message = data["message"].strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Fetch conversation history for this session
    history = get_history(session_id)

    # Get Helena's reply from Gemini (or a snarky error fallback)
    reply = get_reply(history, user_message)

    # Persist the exchange in the session store
    update_history(session_id, user_message, reply)

    return jsonify({"reply": reply})


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
