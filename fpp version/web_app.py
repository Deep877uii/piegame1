from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import json
import csv
from datetime import datetime
import threading
import time
import random
import operator
import base64
from PIL import Image
import io
from config import get_config, find_available_port

app = Flask(__name__)

# Constants
USER_FILE = "users.csv"
QUESTIONS_FILE = "questions.json"  # Changed to JSON file
SESSIONS_DIR = "sessions"
UPLOAD_FOLDER = "static/uploads"

# Ensure required directories exist
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def load_questions():
    questions = []
    test_config = {}
    try:
        if not os.path.exists(QUESTIONS_FILE):
            print(f"Error: {QUESTIONS_FILE} not found. Please create it with the specified format.")
            return questions, test_config
            
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            test_config = {
                "title": data.get("title", "Math Test"),
                "time": int(data.get("Time", "60")),
                "difficulty": int(data.get("Difficulty", "2")),
                "min_questions": int(data.get("MinQuestion", "3"))
            }
            
            for q in data.get("questions", []):
                try:
                    # Handle image path
                    image_path = q.get("image", "")
                    image_data = None
                    
                    if image_path and os.path.exists(image_path):
                        # Convert image to base64 for web display
                        with open(image_path, "rb") as img_file:
                            image_data = base64.b64encode(img_file.read()).decode('utf-8')
                    
                    questions.append({
                        'text': q.get("text", ""),
                        'image': image_data,
                        'answer': q.get("answer", ""),
                        'difficulty': int(q.get("difficulty", "2"))
                    })
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping invalid question: {e}")
                    continue
                    
        if not questions:
            print(f"Error: No valid questions found in {QUESTIONS_FILE}")
            
    except Exception as e:
        print(f"Error loading questions: {e}")
    return questions, test_config

# Game state
questions, test_config = load_questions()
game_state = {
    "players": {},
    "current_problems": {},
    "questions": questions,
    "test_config": test_config,
    "difficulty_levels": {
        "easy": 1,
        "medium": 2,
        "hard": 3
    },
    "current_question_index": {}  # Track current question for each player
}

def get_users_data():
    users = []
    try:
        if not os.path.exists(USER_FILE):
            with open(USER_FILE, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["UserID", "Playtime", "CorrectAnswers", "WrongAnswers", "TotalScore", "Name", "LastPlayed"])
            return users
        
        with open(USER_FILE, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                users.append(row)
    except Exception as e:
        print(f"Error reading users data: {e}")
    return users

def save_user_data(user_data):
    try:
        with open(USER_FILE, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["UserID", "Playtime", "CorrectAnswers", "WrongAnswers", "TotalScore", "Name", "LastPlayed"])
            writer.writeheader()
            writer.writerows(user_data)
    except Exception as e:
        print(f"Error saving user data: {e}")

def save_session_data(session_data):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SESSIONS_DIR}/session_{timestamp}.json"
        with open(filename, "w") as file:
            json.dump(session_data, file, indent=4)
    except Exception as e:
        print(f"Error saving session data: {e}")

def generate_math_problem(difficulty_level):
    # Get all questions
    all_questions = game_state["questions"]
    
    # If no questions available, return an error
    if not all_questions:
        print("Error: No questions available. Please check questions.json file.")
        return "Error: No questions available", 0, None
    
    # Get the current question index for the player
    player_id = request.args.get('userId')
    if player_id not in game_state["current_question_index"]:
        game_state["current_question_index"][player_id] = 0
    
    current_index = game_state["current_question_index"][player_id]
    
    # If we've gone through all questions, start over
    if current_index >= len(all_questions):
        current_index = 0
        game_state["current_question_index"][player_id] = 0
    
    # Get the current question
    question = all_questions[current_index]
    
    # Increment the question index for next time
    game_state["current_question_index"][player_id] = current_index + 1
    
    return question['text'], question['answer'], question['image']

@app.route('/')
def index():
    return render_template('game.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/game/state')
def get_game_state():
    return jsonify(game_state)

@app.route('/api/game/join', methods=['POST'])
def join_game():
    data = request.json
    user_id = data.get('userId')
    name = data.get('name')
    difficulty = data.get('difficulty', 'medium')  # Default to medium if not specified
    
    if user_id and name:
        game_state["players"][user_id] = {
            "name": name,
            "position": 0,
            "score": 0,
            "alive": True,
            "difficulty": difficulty,
            "correct_answers": 0,
            "wrong_answers": 0,
            "questions_answered": 0
        }
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/api/game/move', methods=['POST'])
def move_player():
    data = request.json
    user_id = data.get('userId')
    answer = data.get('answer')
    
    if user_id not in game_state["players"]:
        return jsonify({"status": "error", "message": "Player not found"}), 404
    
    player = game_state["players"][user_id]
    if not player["alive"]:
        return jsonify({"status": "error", "message": "Player eliminated"}), 400
    
    # Check if the answer is correct
    current_problem = game_state["current_problems"].get(user_id)
    if not current_problem:
        return jsonify({"status": "error", "message": "No active problem"}), 400
    
    correct_answer = current_problem[1]
    is_correct = answer.upper() == correct_answer.upper()
    
    # Update player position and score based on answer correctness
    if is_correct:
        player["position"] += 1  # Move forward one step
        player["score"] += 10
        player["correct_answers"] = player.get("correct_answers", 0) + 1
    else:
        player["wrong_answers"] = player.get("wrong_answers", 0) + 1
    
    # Always increment questions answered counter
    player["questions_answered"] = player.get("questions_answered", 0) + 1
    
    # Check if player has answered minimum required questions
    min_questions = game_state["test_config"].get("min_questions", 5)
    can_finish = player["questions_answered"] >= min_questions
    
    # Generate new problem
    problem, answer, image = generate_math_problem(player["difficulty"])
    game_state["current_problems"][user_id] = (problem, answer, image)
    
    # Get current question number
    current_question = game_state["current_question_index"].get(user_id, 0) + 1
    total_questions = len(game_state["questions"])
    
    return jsonify({
        "status": "success",
        "position": player["position"],
        "alive": player["alive"],
        "score": player["score"],
        "next_problem": problem,
        "next_image": image,
        "can_finish": can_finish,
        "questions_answered": player["questions_answered"],
        "min_questions": min_questions,
        "current_question": current_question,
        "total_questions": total_questions,
        "is_correct": is_correct
    })

@app.route('/api/game/problem', methods=['GET'])
def get_problem():
    user_id = request.args.get('userId')
    if not user_id or user_id not in game_state["players"]:
        return jsonify({"status": "error", "message": "Invalid player"}), 400
    
    player = game_state["players"][user_id]
    if user_id not in game_state["current_problems"]:
        problem, answer, image = generate_math_problem(player["difficulty"])
        game_state["current_problems"][user_id] = (problem, answer, image)
    else:
        problem, _, image = game_state["current_problems"][user_id]
    
    # Check if player has answered minimum required questions
    min_questions = game_state["test_config"].get("min_questions", 3)
    can_finish = player["questions_answered"] >= min_questions
    
    # Get current question number
    current_question = game_state["current_question_index"].get(user_id, 0) + 1
    total_questions = len(game_state["questions"])
    
    return jsonify({
        "status": "success",
        "problem": problem,
        "image": image,
        "can_finish": can_finish,
        "questions_answered": player["questions_answered"],
        "min_questions": min_questions,
        "current_question": current_question,
        "total_questions": total_questions
    })

@app.route('/api/dashboard/users')
def get_users():
    return jsonify(get_users_data())

@app.route('/api/dashboard/sessions')
def get_sessions():
    sessions = []
    try:
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(SESSIONS_DIR, filename), 'r') as file:
                    sessions.append(json.load(file))
    except Exception as e:
        print(f"Error reading sessions: {e}")
    return jsonify(sessions)

if __name__ == '__main__':
    # This block will only run if the file is executed directly
    # When imported by launcher.py, this block won't run
    config = get_config()
    
    # Try to use the configured port
    port = config['PORT']
    try:
        app.run(host=config['HOST'], port=port, debug=True)
    except OSError:
        # If port is in use, try to find an available port in the range
        print(f"Port {port} is in use. Trying to find an available port...")
        available_port = find_available_port(*config['PORT_RANGE'])
        if available_port:
            print(f"Found available port: {available_port}")
            app.run(host=config['HOST'], port=available_port, debug=True)
        else:
            print(f"Error: Could not find an available port in range {config['PORT_RANGE']}")
            exit(1) 