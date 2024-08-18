from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import openai
import os
from dotenv import load_dotenv
from gtts import gTTS
import whisper

# Load environment variables
load_dotenv('.env.local')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or 'your_secret_key_here'  # Replace with a strong key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load Whisper model
whisper_model = whisper.load_model("base")

# Database model for storing users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return 'Login failed. Check your credentials.'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "This email is already registered. Please use a different email or log in."

        # If the email is not registered, add the new user
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/process_audio', methods=['POST'])
def process_audio_endpoint():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    audio_path = os.path.join("static/uploads", audio_file.filename)
    audio_file.save(audio_path)

    response_text = process_audio_with_gpt(audio_path)

    return jsonify({
        "response_text": response_text,
        "audio_url": "/static/response.mp3"
    })

def process_audio_with_gpt(audio_file):
    try:
        # Transcribe audio using Whisper
        result = whisper_model.transcribe(audio_file)
        recognized_text = result.get("text", "").lower()

        if not recognized_text:
            return "Sorry, I couldn't understand that."

        # Generate response with OpenAI GPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": recognized_text}
            ]
        )
        response_text = response['choices'][0]['message']['content'].strip()

        # Use gTTS to generate the voice response
        tts = gTTS(response_text)
        tts.save("static/response.mp3")

        return response_text

    except Exception as e:
        return f"Error processing audio: {e}"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
