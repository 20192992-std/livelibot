from flask import Blueprint, render_template, request, jsonify, current_app

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()

    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    print(f"User: {message}")

    try:
        assistant = current_app.extensions["assistant"]
        result = assistant.ask(message)

        print(result)

        if result["sources"]:
            reply = result["answer"]
        else:
            reply = assistant.normal_message(message)

        return jsonify({"reply": reply, "sources": result["sources"]})

    except Exception as error:
        print(f"Chat error: {error}")

        return jsonify({
            "error": "Something went wrong while processing your question."
        }), 500

    return jsonify({
        "reply": "Message received!"
    })