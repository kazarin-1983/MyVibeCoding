import pytest

from app import app


@pytest.fixture
def client():
    """
    Фикстура: создаёт тестовый клиент Flask.
    Используется во всех тестах, чтобы не поднимать реальный сервер.
    """
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def first_quiz_id(client):
    """Возвращает id первой доступной викторины — используется в тестах прогресса."""
    quizzes = client.get("/api/quizzes").get_json()
    return quizzes[0]["id"]


# ─────────────────────────────────────────────────────────────
# 1. Список викторин
# ─────────────────────────────────────────────────────────────

def test_quizzes_endpoint_returns_list(client):
    """GET /api/quizzes должен вернуть список викторин."""
    response = client.get("/api/quizzes")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_every_quiz_has_id_and_title(client):
    """У каждой викторины в списке должны быть поля id и title."""
    response = client.get("/api/quizzes")
    data = response.get_json()

    for quiz in data:
        assert "id" in quiz
        assert "title" in quiz
        assert isinstance(quiz["id"], str)
        assert isinstance(quiz["title"], str)


# ─────────────────────────────────────────────────────────────
# 2. Вопросы викторины
# ─────────────────────────────────────────────────────────────

def test_questions_for_existing_quiz(client):
    """GET /api/questions/<id> возвращает список вопросов для существующей темы."""
    quizzes = client.get("/api/quizzes").get_json()
    assert len(quizzes) > 0

    quiz_id = quizzes[0]["id"]

    response = client.get(f"/api/questions/{quiz_id}")

    assert response.status_code == 200
    questions = response.get_json()
    assert isinstance(questions, list)
    assert len(questions) > 0


def test_questions_have_required_fields(client):
    """У каждого вопроса должны быть question, options, answer, id."""
    quizzes = client.get("/api/quizzes").get_json()
    quiz_id = quizzes[0]["id"]

    questions = client.get(f"/api/questions/{quiz_id}").get_json()

    for q in questions:
        assert "id" in q
        assert "question" in q
        assert "options" in q
        assert "answer" in q
        assert isinstance(q["options"], list)
        assert len(q["options"]) >= 2
        assert q["answer"] in q["options"]


def test_questions_for_unknown_quiz_returns_404(client):
    """GET /api/questions/<несуществующая_тема> должен вернуть 404."""
    response = client.get("/api/questions/this_quiz_does_not_exist")

    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


# ─────────────────────────────────────────────────────────────
# 3. Прогресс
# ─────────────────────────────────────────────────────────────

def test_progress_default_on_first_visit(client, first_quiz_id):
    """GET /api/progress/<id> при первом заходе отдаёт дефолтный прогресс."""
    response = client.get(f"/api/progress/{first_quiz_id}")

    assert response.status_code == 200
    data = response.get_json()
    assert data == {
        "round": 1,
        "score": 0,
        "answered_ids": [],
        "finished": False,
    }


def test_progress_saves_round_and_score(client, first_quiz_id):
    """POST /api/progress/<id> сохраняет round, score, answered_ids."""
    payload = {
        "round": 3,
        "score": 2,
        "answered_ids": [0, 4],
        "finished": False,
    }

    response = client.post(f"/api/progress/{first_quiz_id}", json=payload)
    assert response.status_code == 200
    assert response.get_json() == payload

    # Читаем обратно — прогресс должен сохраниться
    again = client.get(f"/api/progress/{first_quiz_id}")
    assert again.get_json() == payload


def test_reset_restores_default_progress(client, first_quiz_id):
    """POST /api/reset/<id> сбрасывает прогресс до дефолта."""
    # Сначала испортим прогресс
    client.post(
        f"/api/progress/{first_quiz_id}",
        json={"round": 5, "score": 4, "answered_ids": [0, 1, 2, 3], "finished": True},
    )

    # Сбрасываем
    response = client.post(f"/api/reset/{first_quiz_id}")
    assert response.status_code == 200
    assert response.get_json() == {
        "round": 1,
        "score": 0,
        "answered_ids": [],
        "finished": False,
    }


def test_progress_isolated_between_quizzes(client):
    """Прогресс по одной теме не влияет на прогресс по другой."""
    quizzes = client.get("/api/quizzes").get_json()
    if len(quizzes) < 2:
        pytest.skip("Нужно минимум две викторины для этого теста")

    id_a = quizzes[0]["id"]
    id_b = quizzes[1]["id"]

    # Меняем прогресс только у первой
    client.post(f"/api/progress/{id_a}", json={"score": 99})

    # Проверяем, что у второй он дефолтный
    progress_b = client.get(f"/api/progress/{id_b}").get_json()
    assert progress_b["score"] == 0