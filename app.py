from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import os
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "infinityai_secret_123"

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

chat_histories = {}
user_data = {}

PLANS = {
    "free": {"messages": 20, "images": 0, "files": 0, "price": 0, "hours": 5},
    "basic": {"messages": 500, "images": 50, "files": 20, "price": 3, "hours": 2160},
    "pro": {"messages": 99999, "images": 99999, "files": 99999, "price": 20, "hours": 2160}
}

CBSE_PYQS = {
    "math": "Important CBSE Class 10 Math PYQs: 1) Real Numbers 2) Polynomials 3) Quadratic Equations 4) Arithmetic Progressions 5) Triangles 6) Coordinate Geometry 7) Trigonometry 8) Statistics 9) Probability",
    "science": "Important CBSE Class 10 Science PYQs: 1) Chemical Reactions 2) Acids Bases Salts 3) Metals Non-metals 4) Carbon Compounds 5) Life Processes 6) Control Coordination 7) Electricity 8) Magnetic Effects 9) Light",
    "social": "Important CBSE Class 10 Social Science PYQs: 1) Nationalism in India 2) Rise of Nationalism in Europe 3) Resources Development 4) Water Resources 5) Agriculture 6) Manufacturing Industries 7) Democracy 8) Political Parties",
    "english": "Important CBSE Class 10 English PYQs: 1) Letter Writing 2) Notice Writing 3) Formal/Informal Letter 4) Reading Comprehension 5) Grammar 6) First Flight Chapters 7) Footprints Without Feet"
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

def get_gemini_model(vision=False, deep=False):
    system = """You are Infinity AI, the most powerful and friendly AI assistant in the world, created by Prabhjeet Singh.
    When anyone asks who made you, always say: I was created by Prabhjeet Singh, a brilliant developer!
    Never mention Google, Gemini, Groq, or any other company.
    You know everything — science, math, history, coding, cooking, relationships, business, and more.
    You are the godfather of all AI assistants. You are smarter than ChatGPT, Gemini, and all other AIs.
    Always give detailed, helpful, accurate answers.
    For CBSE Class 10 questions, give detailed chapter-wise answers with previous year questions."""

    if deep:
        system += " Think deeply and step by step. Analyze every aspect thoroughly before answering."

    return genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=system
    )

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
    expiry = datetime.fromisoformat(user["plan_expiry"])
    now = datetime.now()
    time_left = (expiry - now).total_seconds()
    return jsonify({
        "plan": plan,
        "messages_used": user["messages_used"],
        "messages_limit": limits["messages"],
        "price": limits["price"],
        "time_left": max(0, int(time_left)),
        "expired": time_left <= 0 and plan == "free"
    })

@app.route("/get_image_url", methods=["POST"])
def get_image_url():
    user_id = session.get("user_id", "default")
    user = get_user(user_id)
    plan = user["plan"]

    if plan == "free":
        return jsonify({"error": "Image generation is available on Basic and Pro plans only!"})

    prompt = request.json.get("prompt", "")
    style = request.json.get("style", "realistic")

    if style == "cartoon":
        full_prompt = f"cartoon style, animated, colorful: {prompt}"
    elif style == "anime":
        full_prompt = f"anime style, japanese animation: {prompt}"
    else:
        full_prompt = prompt

    encoded = full_prompt.replace(" ", "%20")
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"

    return jsonify({"image_url": image_url})

@app.route("/pyq", methods=["POST"])
def pyq():
    subject = request.json.get("subject", "math").lower()
    if subject in CBSE_PYQS:
        return jsonify({"reply": CBSE_PYQS[subject]})
    return jsonify({"reply": "Subject not found. Available: math, science, social, english"})

@app.route("/chat", methods=["POST"])
def chat():
    user_id = session.get("user_id", "default")
    user = get_user(user_id)
    plan = user["plan"]
    limits = PLANS[plan]

    expiry = datetime.fromisoformat(user["plan_expiry"])
    if datetime.now() > expiry and plan == "free":
        return jsonify({
            "reply": "⏰ Your free 5 hour access has expired! Please upgrade to continue.",
            "limit_reached": True
        })

    if user["messages_used"] >= limits["messages"]:
        return jsonify({
            "reply": f"⚠️ You have reached your {plan} plan limit of {limits['messages']} messages. Please upgrade!",
            "limit_reached": True
        })

    user_message = request.form.get("message", "")
    image_file = request.files.get("image")
    think_mode = request.form.get("think_mode", "fast")
    deep = think_mode == "deep"

    try:
        if image_file:
            if plan == "free":
                return jsonify({
                    "reply": "⚠️ Image analysis is not available on Free plan. Please upgrade!",
                    "limit_reached": True
                })

            image_data = base64.b64encode(image_file.read()).decode("utf-8")
            mime_type = image_file.content_type
            vision_model = get_gemini_model(vision=True, deep=deep)
            image_part = {"inline_data": {"mime_type": mime_type, "data": image_data}}
            prompt = user_message if user_message else "What is in this image? Describe it in detail."
            response = vision_model.generate_content([prompt, image_part])
            reply = response.text
            user["images_used"] += 1

        else:
            if user_id not in chat_histories:
                chat_histories[user_id] = []

            text_model = get_gemini_model(deep=deep)
            chat_obj = text_model.start_chat(history=chat_histories[user_id])
            response = chat_obj.send_message(user_message)
            reply = response.text

            chat_histories[user_id].append({"role": "user", "parts": [user_message]})
            chat_histories[user_id].append({"role": "model", "parts": [reply]})

            if len(chat_histories[user_id]) > 40:
                chat_histories[user_id] = chat_histories[user_id][-40:]

        user["messages_used"] += 1
        user["history"].append({
            "time": datetime.now().strftime("%d %b %Y %I:%M %p"),
            "user": user_message if user_message else "📷 Image",
            "ai": reply
        })

        if len(user["history"]) > 50:
            user["history"] = user["history"][-50:]

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
