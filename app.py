import os
import requests
from flask import Flask, request, jsonify, render_template, session

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed to store session data

# ✅ Load Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ✅ Fetch banned words from external source
BANNED_WORDS_URL = "http://www.bannedwordlist.com/lists/swearWords.txt"

def fetch_banned_words():
    """Fetch banned words from the external source."""
    try:
        response = requests.get(BANNED_WORDS_URL)
        if response.status_code == 200:
            return set(response.text.splitlines())  # Store as a set for fast lookup
    except Exception as e:
        print("Error fetching banned words:", str(e))
    return set()

# ✅ Load banned words on startup
BANNED_WORDS = fetch_banned_words()

def is_message_inappropriate(user_input):
    """Check if user input contains banned words."""
    words = user_input.lower().split()
    return any(word in BANNED_WORDS for word in words)

def ask_groq(user_input):
    """Send a query to Groq API with conversation history."""
    if not GROQ_API_KEY:
        return "Error: Groq API key is missing."

    # ✅ Check for inappropriate content
    if is_message_inappropriate(user_input):
        return "Please keep the conversation respectful."

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # ✅ Retrieve chat history from session
    if "chat_history" not in session:
        session["chat_history"] = []

    # ✅ Append user message to chat history
    session["chat_history"].append({"role": "user", "content": user_input})

    # ✅ Keep only the last 5 messages for context
    session["chat_history"] = session["chat_history"][-5:]

    data = {
        "model": "llama3-8b-8192",  # ✅ Supported Groq model
        "messages": [{"role": "system", "content": "You are a knowledgeable AI yoga instructor."}] + session["chat_history"],
        "temperature": 0.7,
        "max_tokens": 200
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()

        if "choices" in response_json:
            ai_response = response_json["choices"][0]["message"]["content"].strip()
            session["chat_history"].append({"role": "assistant", "content": ai_response})  # ✅ Store AI response
            return ai_response
        else:
            return "Error: Unexpected API response."

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chatbot requests."""
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message.strip():
        return jsonify({"response": "Please ask a valid question."})

    ai_response = ask_groq(user_message)
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(debug=True)
