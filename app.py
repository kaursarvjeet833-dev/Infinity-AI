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

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "plan": "free",
            "messages_used": 0,
