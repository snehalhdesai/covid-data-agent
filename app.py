from flask import Flask, request, jsonify, render_template
from config import APP_PORT, DEBUG
from agent import create_assistant, create_thread, ask

app = Flask(__name__)
assistant = create_assistant()
thread = create_thread()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask_route():
    question = request.json.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question"}), 400
    result = ask(thread.id, assistant.id, question)
    return jsonify(result)

@app.route("/reset", methods=["POST"])
def reset():
    global thread
    thread = create_thread()
    return jsonify({"status": "reset", "thread_id": thread.id})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "assistant_id": assistant.id, "thread_id": thread.id})

if __name__ == "__main__":
    app.run(debug=DEBUG, port=APP_PORT)
