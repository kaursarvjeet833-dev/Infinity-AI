
from flask import Flask, render_template, request, jsonify, session
from groq import Groq
import os
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "infinityai_secret_123"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

chat_histories = {}
user_data = {}

PLANS = {
    "free": {"messages": 20, "images": 0, "files": 0, "price": 0, "hours": 5},
    "pro": {"messages": 500, "images": 50, "files": 20, "price": 2, "hours": 2160},
    "max": {"messages": 99999, "images": 99999, "files": 99999, "price": 20, "hours": 2160}
}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "plan": "free",
            "messages_used": 0,
            "images_used": 0,
            "files_used": 0,
            "history": [],
            "first_visit": datetime.now().isoformat(),
            "plan_expiry": (datetime.now() + timedelta(hours=5)).isoformat()
        }
    return user_data[user_id]

@app.route("/")
def home():
    if "user_id" not in session:
        session["user_id"] = os.urandom(8).hex()
    return render_template("index.html")

@app.route("/get_history", methods=["GET"])
def get_history():
    user_id = session.get("user_id", "default")
    user = get_user(user_id)
    return jsonify({"history": user["history"], "plan": user["plan"]})

@app.route("/get_plan", methods=["GET"])
def get_plan():
    user_id = session.get("user_id", "default")
    user = get_user(user_id)
    plan = user["plan"]
    limits = PLANS[plan]

    # Check time expiry
    expiry = datetime.fromisoformat(user["plan_expiry"])
    now = datetime.now()
    time_left = (expiry - now).total_seconds()

    return jsonify({
        "plan": plan,
        "messages_used": user["messages_used"],
        "messages_limit": limits["messages"],
        "price": limits["price"],
        "time_left": max(0, int(time_left)),
        "expired": time_left <= 0
    })

@app.route("/chat", methods=["POST"])
def chat():
    user_id = session.get("user_id", "default")
    user = get_user(user_id)
    plan = user["plan"]
    limits = PLANS[plan]

    # Check time expiry
    expiry = datetime.fromisoformat(user["plan_expiry"])
    if datetime.now() > expiry:
        return jsonify({"reply": "⏰ Your free 5 hour access has expired! Please upgrade to continue.", "limit_reached": True})

    # Check message limit
    if user["messages_used"] >= limits["messages"]:
        return jsonify({"reply": f"⚠️ You have reached your {plan} plan limit of {limits['messages']} messages. Please upgrade!", "limit_reached": True})

    user_message = request.form.get("message", "")
    image_file = request.files.get("image")

    if user_id not in chat_histories:
        chat_histories[user_id] = [
            {"role": "system", "content": "You are Infinity AI, a powerful and friendly AI assistant created by Prabhjeet Singh. When anyone asks who made you, always say: I was created by Prabhjeet Singh, a brilliant developer!"}
        ]

    try:
        if image_file and plan != "free":
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
            mime_type = image_file.content_type
            messages = [
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                    {"type": "text", "text": user_message if user_message else "What is in this image?"}
                ]}
            ]
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                max_tokens=1024
            )
            user["images_used"] += 1
        elif image_file and plan == "free":
            return jsonify({"reply": "⚠️ Image upload is not available on Free plan. Please upgrade to Basic or Pro!", "limit_reached": True})
        else:
            chat_histories[user_id].append({"role": "user", "content": user_message})
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=chat_histories[user_id],
                max_tokens=1024
            )
            chat_histories[user_id].append({
                "role": "assistant",
                "content": response.choices[0].message.content
            })

        reply = response.choices[0].message.content
        user["messages_used"] += 1

        user["history"].append({
            "time": datetime.now().strftime("%d %b %Y %I:%M %p"),
            "user": user_message,
            "ai": reply
        })

        if len(user["history"]) > 50:
            user["history"] = user["history"][-50:]

        # Check time left
        expiry = datetime.fromisoformat(user["plan_expiry"])
        time_left = max(0, int((expiry - datetime.now()).total_seconds()))

        return jsonify({
            "reply": reply,
            "messages_used": user["messages_used"],
            "messages_limit": limits["messages"],
            "time_left": time_left
        })

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
