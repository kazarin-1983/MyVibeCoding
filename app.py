import json
from pathlib import Path
from flask import Flask, render_template, jsonify, request, session

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

# Абсолютный путь к папке с викторинами.
# BASE_DIR — это папка, где лежит сам app.py (например, /home/Fixius/MyVibeCoding).
# Так работает и локально, и на PythonAnywhere, и на любом другом хостинге.
BASE_DIR = Path(__file__).resolve().parent
QUIZZES_DIR = BASE_DIR / "quizzes"

# Загружаем все викторины при старте.
# Структура: {"metro": [вопросы...], "construction": [вопросы...]}
QUIZZES = {}
for path in sorted(QUIZZES_DIR.glob("*.json")):
    quiz_id = path.stem  # "metro.json" -> "metro"
    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)
    for idx, q in enumerate(questions):
        q["id"] = idx
    QUIZZES[quiz_id] = questions


def default_progress():
    return {
        "round": 1,
        "score": 0,
        "answered_ids": [],
        "finished": False,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/quizzes")
def get_quizzes():
    """Список доступных викторин с человекочитаемыми названиями."""
    names = {
        "metro": "Метро",
        "construction": "Строительная техника",
    }
    return jsonify([
        {"id": quiz_id, "title": names.get(quiz_id, quiz_id)}
        for quiz_id in QUIZZES.keys()
    ])


@app.route("/api/questions/<quiz_id>")
def get_questions(quiz_id):
    if quiz_id not in QUIZZES:
        return jsonify({"error": "Викторина не найдена"}), 404
    return jsonify(QUIZZES[quiz_id])


@app.route("/api/progress/<quiz_id>", methods=["GET", "POST"])
def progress(quiz_id):
    if quiz_id not in QUIZZES:
        return jsonify({"error": "Викторина не найдена"}), 404

    # Прогресс хранится в сессии отдельно для каждой викторины:
    # session["progress"] = {"metro": {...}, "construction": {...}}
    all_progress = session.get("progress", {})
    data = all_progress.get(quiz_id) or default_progress()

    if request.method == "GET":
        all_progress[quiz_id] = data
        session["progress"] = all_progress
        return jsonify(data)

    payload = request.get_json(silent=True) or {}
    if "round" in payload:
        data["round"] = int(payload["round"])
    if "score" in payload:
        data["score"] = int(payload["score"])
    if "answered_ids" in payload:
        data["answered_ids"] = list(payload["answered_ids"])
    if "finished" in payload:
        data["finished"] = bool(payload["finished"])

    all_progress[quiz_id] = data
    session["progress"] = all_progress
    return jsonify(data)


@app.route("/api/reset/<quiz_id>", methods=["POST"])
def reset(quiz_id):
    if quiz_id not in QUIZZES:
        return jsonify({"error": "Викторина не найдена"}), 404

    all_progress = session.get("progress", {})
    all_progress[quiz_id] = default_progress()
    session["progress"] = all_progress
    return jsonify(all_progress[quiz_id])


if __name__ == "__main__":
    app.run(debug=True)