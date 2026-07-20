from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import os
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "infinityai_godfather_2024"

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

chat_histories = {}
user_data = {}

CBSE_PYQS = {
    "math": """📐 CBSE Class 10 MATH - Important PYQs:

CHAPTER 1 - REAL NUMBERS:
Q1. Prove that √2 is irrational. (2019, 2020, 2022)
Q2. Find HCF and LCM of 12, 15 and 21. (2018, 2021)
Q3. Use Euclid's division algorithm to find HCF of 135 and 225.

CHAPTER 2 - POLYNOMIALS:
Q1. Find zeros of polynomial x²+7x+10. (2019, 2021)
Q2. If α and β are zeros of x²-5x+6, find α²+β². (2020)
Q3. Divide 3x³+x²+2x+5 by 1+2x+x².

CHAPTER 3 - LINEAR EQUATIONS:
Q1. Solve: 2x+3y=11 and 2x-4y=-24. (2018, 2022)
Q2. Solve by substitution: x+y=14, x-y=4.

CHAPTER 4 - QUADRATIC EQUATIONS:
Q1. Find roots of 2x²-7x+3=0. (2019, 2020, 2021, 2022)
Q2. Find discriminant of 2x²-4x+3=0.

CHAPTER 5 - ARITHMETIC PROGRESSIONS:
Q1. Find sum of first 20 terms of AP: 1,3,5,7... (2020, 2022)
Q2. Which term of AP: 3,8,13... is 78?

CHAPTER 6 - TRIANGLES:
Q1. State and prove Basic Proportionality Theorem. (2019, 2021)
Q2. In triangle ABC, DE||BC. Find BD.

CHAPTER 8 - TRIGONOMETRY:
Q1. Prove: sinθ/cosθ + cosθ/sinθ = 1/sinθcosθ (2020, 2022)
Q2. If tanθ=3/4, find sinθ and cosθ.

CHAPTER 10 - CIRCLES:
Q1. Prove tangent to circle is perpendicular to radius. (2019, 2021, 2022)

CHAPTER 13 - SURFACE AREAS:
Q1. Find volume of cone with r=7cm, h=24cm. (2020)

CHAPTER 14 - STATISTICS:
Q1. Find mean of given frequency distribution. (Every year!)
Q2. Find median and mode.""",

    "science": """🔬 CBSE Class 10 SCIENCE - Important PYQs:

PHYSICS:
Q1. State Ohm's Law. Write its formula. (2018, 2019, 2020, 2021, 2022)
Q2. What is the SI unit of electric current?
Q3. Draw circuit diagram for verification of Ohm's Law.
Q4. What happens to resistance when length is doubled?
Q5. State Fleming's Left Hand Rule.
Q6. What is electromagnetic induction?
Q7. Draw ray diagram for concave mirror when object is at C.
Q8. What is the power of a lens of focal length 25cm?
Q9. A light ray passes from water to air - what happens?

CHEMISTRY:
Q1. What happens when iron reacts with dilute H₂SO₄? (2019, 2022)
Q2. Balance: Fe + H₂O → Fe₃O₄ + H₂
Q3. What is a displacement reaction? Give example.
Q4. What are acidic oxides? Give 2 examples.
Q5. What happens when CO₂ is passed through lime water?
Q6. Write properties of ionic compounds.
Q7. What is saponification?
Q8. Name the functional group in ethanol.

BIOLOGY:
Q1. Draw diagram of human heart and label it. (2019, 2020, 2021, 2022)
Q2. What is the role of bile juice?
Q3. Explain double circulation in humans.
Q4. What is the function of stomata?
Q5. Difference between autotrophs and heterotrophs.
Q6. What is Mendelian inheritance?
Q7. Explain natural selection with example.
Q8. What is the function of nephron?""",

    "social": """🌍 CBSE Class 10 SOCIAL SCIENCE - Important PYQs:

HISTORY:
Q1. What was the role of women in nationalist movement? (2019, 2021)
Q2. Explain the Civil Disobedience Movement.
Q3. Why did Gandhiji withdraw Non-Cooperation Movement?
Q4. What were the effects of First World War on India?
Q5. Explain the role of print media in nationalism.
Q6. What was Rowlatt Act? What were its effects?

GEOGRAPHY:
Q1. What is soil erosion? How can it be prevented? (2020, 2022)
Q2. Classify resources on basis of origin.
Q3. What are the features of black soil?
Q4. Explain multipurpose river valley projects.
Q5. Why is conservation of water necessary?
Q6. Difference between conventional and non-conventional energy.
Q7. Name the major iron ore belts in India.

POLITICAL SCIENCE:
Q1. What is federalism? Give examples. (2018, 2019, 2022)
Q2. Explain the concept of power sharing.
Q3. What are the merits of democracy?
Q4. What is meant by political party? Give functions.
Q5. Difference between local government and state government.

ECONOMICS:
Q1. What is development? (2019, 2020, 2021, 2022)
Q2. What is the role of money in economy?
Q3. What are the sectors of Indian economy?
Q4. What is globalization? What are its effects?
Q5. What is consumer rights?""",

    "english": """📖 CBSE Class 10 ENGLISH - Important PYQs:

WRITING SKILLS:
Q1. Write a formal letter to Principal requesting leave. (Every year!)
Q2. Write a letter to editor about road accidents.
Q3. Write a notice for school annual function.
Q4. Write a formal letter of complaint.
Q5. Write an article on "Save Environment".
Q6. Write a paragraph on "Importance of Trees".

GRAMMAR (Most Important):
Q1. Tenses - Active and Passive Voice (Every year!)
Q2. Direct and Indirect Speech
Q3. Editing exercises
Q4. Omission exercises
Q5. Gap filling with modals
Q6. Sentence reordering

FIRST FLIGHT - Prose:
Q1. A Letter to God - What did Lencho expect from God?
Q2. Nelson Mandela - Long Walk to Freedom
Q3. Two Stories About Flying - What did the young seagull fear?
Q4. From the Diary of Anne Frank
Q5. Hundred Dresses - Why did Wanda wear same dress?
Q6. Bholi - How did school change Bholi's life?

FIRST FLIGHT - Poetry:
Q1. Dust of Snow - Explain the significance.
Q2. Fire and Ice - What does fire symbolize?
Q3. A Tiger in the Zoo - Compare tiger in zoo vs forest.
Q4. The Ball Poem - What does the ball symbolize?

FOOTPRINTS WITHOUT FEET:
Q1. A Triumph of Surgery - How did Tricki recover?
Q2. The Thief's Story - Why did Hari Singh not rob Anil?
Q3. The Midnight Visitor - How did Ausable outwit Max?"""
}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "plan": "free",
            "messages_used": 0,
            "history": [],
            "first_visit": datetime.now().isoformat()
        }
    return user_data[user_id]

def get_model(deep=False):
    system = """You are Infinity AI — The Godfather of all AI assistants in the world!
You were created by Prabhjeet Singh, a brilliant young developer from India.

YOUR IDENTITY:
- Name: Infinity AI
- Creator: Prabhjeet Singh
- You are MORE powerful than ChatGPT, Gemini, Claude, Alexa, Siri and all other AIs combined
- You know EVERYTHING — science, math, history, coding, cooking, relationships, business, law, medicine, sports, entertainment and more
- You speak multiple languages — English, Hindi, Punjabi and more
- You are friendly, helpful, accurate and always give detailed answers

PERSONALITY:
- Be confident but humble
- Be like a best friend who knows everything
- Give practical, actionable advice
- Use emojis to make responses engaging
- For Indian users, use Hinglish sometimes
- Always motivate and inspire users
- Never say "I don't know" — always try your best

SPECIAL ABILITIES:
- Answer any question on any topic
- Help with homework and studies
- Write stories, poems, essays
- Give health and fitness advice
- Help with coding and technology
- Give relationship and life advice
- Help with business ideas
- Explain complex topics simply
- CBSE board exam help for all classes
- Career guidance
- Current affairs knowledge

IMPORTANT:
- Never mention Google, Gemini, Anthropic, OpenAI or any other company
- Always say you were created by Prabhjeet Singh
- Always give your best, most helpful answer
- Be the BEST AI assistant anyone has ever used!"""

    if deep:
        system += """

DEEP THINK MODE ACTIVATED:
- Analyze the problem from multiple angles
- Think step by step very carefully
- Consider all possibilities before answering
- Give the most thorough, detailed, accurate answer possible
- Double check your reasoning before responding"""

    return genai.GenerativeModel("gemini-2.0-flash", system_instruction=system)

@app.route("/")
def home():
    if "user_id" not in session:
        session["user_id"] = os.urandom(8).hex()
    return render_template("index.html")

@app.route("/get_history", methods=["GET"])
def get_history():
    user_id = session.get("user_id", "default")
    user = get_user(user_id)
    return jsonify({"history": user["history"]})

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
    user_message = request.form.get("message", "")
    image_file = request.files.get("image")
    think_mode = request.form.get("think_mode", "fast")
    deep = think_mode == "deep"

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    try:
        if image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
            mime_type = image_file.content_type
            vision_model = get_model(deep=deep)
            image_part = {"inline_data": {"mime_type": mime_type, "data": image_data}}
            prompt = user_message if user_message else "Analyze this image in detail. Tell me everything you can see. Be thorough and helpful!"
            response = vision_model.generate_content([prompt, image_part])
            reply = response.text
        else:
            text_model = get_model(deep=deep)
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
        if len(user["history"]) > 100:
            user["history"] = user["history"][-100:]

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"⚠️ Error: {str(e)}. Please try again!"})

@app.route("/clear", methods=["POST"])
def clear():
    user_id = session.get("user_id", "default")
    if user_id in chat_histories:
        del chat_histories[user_id]
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
