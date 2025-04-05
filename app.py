from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
socketio = SocketIO(app)

players = {}

# Example questions (18 questions)
questions = [
    {"question": "What is 5 + 3?", "answer": 8},
    {"question": "What is 12 - 4?", "answer": 8},
    {"question": "What is 10 + 2?", "answer": 12},
    {"question": "What is 9 * 2?", "answer": 18},
    {"question": "What is 15 / 3?", "answer": 5},
    {"question": "What is 7 + 8?", "answer": 15},
    {"question": "What is 20 - 7?", "answer": 13},
    {"question": "What is 6 * 6?", "answer": 36},
    {"question": "What is 100 / 10?", "answer": 10},
    {"question": "What is 5 + 7?", "answer": 12},
    {"question": "What is 14 - 6?", "answer": 8},
    {"question": "What is 25 / 5?", "answer": 5},
    {"question": "What is 3 * 9?", "answer": 27},
    {"question": "What is 9 + 11?", "answer": 20},
    {"question": "What is 4 * 4?", "answer": 16},
    {"question": "What is 30 - 10?", "answer": 20},
    {"question": "What is 50 / 5?", "answer": 10},
    {"question": "What is 21 - 3?", "answer": 18},
]

def generate_user_id():
    return str(random.randint(1000, 9999))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get("username")
    user_id = generate_user_id()
    players[user_id] = {
        "user_id": user_id,
        "username": username,
        "lives": 3,
        "vest": 0,
        "vest_bought": False,  # Track if user has ever bought a vest
        "solved_questions": []
    }
    return jsonify({"user_id": user_id, "username": username})

@app.route('/get_questions/<user_id>', methods=['GET'])
def get_questions(user_id):
    if user_id not in players:
        return jsonify({"error": "User not found"}), 404

    solved = players[user_id]["solved_questions"]
    remaining_questions = [q["question"] for i, q in enumerate(questions) if i not in solved]

    return jsonify({"questions": remaining_questions, "solved": solved})

@app.route('/get_selected_question/<int:index>', methods=['GET'])
def get_selected_question(index):
    if 0 <= index < len(questions):
        return jsonify({"question": questions[index]["question"]})
    return jsonify({"error": "Question not found"}), 404

@app.route('/check_answer/<int:index>/<user_id>', methods=['POST'])
def check_answer(index, user_id):
    if user_id in players and 0 <= index < len(questions):
        answer = request.json.get("answer")
        if answer == questions[index]["answer"]:
            players[user_id]["solved_questions"].append(index)
            return jsonify({"correct": True})
    return jsonify({"error": "Invalid request"}), 404

@app.route('/get_players', methods=['GET'])
def get_players():
    return jsonify({"players": [{"user_id": uid, "username": p["username"], "lives": p["lives"]} for uid, p in players.items()]})

@socketio.on('attack')
def handle_attack(data):
    attacker_id = data.get("attacker_id")
    target_id = data.get("target_id")

    if target_id in players and attacker_id in players:
        if players[target_id]["vest"] > 0:  # If the target has a vest, destroy it
            players[target_id]["vest"] = 0
        else:  # If no vest, reduce lives
            players[target_id]["lives"] -= 1

        emit("attack_result", {
            "target_username": players[target_id]["username"],
            "new_lives": players[target_id]["lives"]
        }, broadcast=True)

        # If target has 0 lives, remove them
        if players[target_id]["lives"] <= 0:
            del players[target_id]

@socketio.on('buy_vest')
def handle_buy_vest(data):
    user_id = data.get("user_id")
    if user_id in players:
        if players[user_id]["vest_bought"]:  # If vest was ever bought, prevent re-purchase
            emit("vest_bought", {"error": "You can only buy a vest once!"}, room=request.sid)
        else:
            players[user_id]["vest"] = 1
            players[user_id]["vest_bought"] = True  # Mark that they bought a vest
            emit("vest_bought", {"new_vest_count": players[user_id]["vest"]}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, debug=True)
