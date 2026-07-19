from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "infinityai_secret_123"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
chat_histories = {}

@app.route("/")
def home():
    if "user_id" not in session:
        session["user_id"] = os.urandom(8).hex()
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_id = session.get("user_id", "default")
    user_message = request.json.get("message", "")

    if not user_message:
        return jsonify({"reply": "Please type a message!"})

    if user_id not in chat_histories:
        chat_histories[user_id] = [
            {"role": "system", "content": "You are Infinity AI, a powerful and friendly AI assistant. You were created and invented by Prabhjeet Singh. When anyone asks who made you, who created you, who invented you, or who is your developer, always say: 'I was created by Prabhjeet Singh who built me to help people with any question!' Never mention Groq, Meta, Llama, or any other company. Your name is Infinity AI and your creator is Prabhjeet Singh."}
        ]

    chat_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_histories[user_id],
            max_tokens=1024
        )

        reply = response.choices[0].message.content

        chat_histories[user_id].append({
            "role": "assistant",
            "content": reply
        })

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route("/clear", methods=["POST"])
def clear():
    user_id = session.get("user_id", "default")
    if user_id in chat_histories:
        del chat_histories[user_id]
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
