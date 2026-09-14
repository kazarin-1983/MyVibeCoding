import json
import time
import requests
from urllib.parse import quote
from pathlib import Path

QUIZZES_DIR = Path("quizzes")
API_URL = "https://commons.wikimedia.org/w/api.php"

# Ключ — текст вопроса, значение — поисковый запрос.
# Для строительной техники у всех вопросов один текст, поэтому
# искать будем по ответу (см. функцию build_search_term).
SEARCH_TERMS = {
    # метро
    "Какая станция московского метро является самой глубокой?": "Park Pobedy Moscow Metro",
    "На какой станции установлены знаменитые 76 бронзовых скульптур?": "Ploshchad Revolyutsii Moscow Metro",
    "Какая линия московского метро обозначается коричневым цветом на схеме?": "Koltsevaya line Moscow Metro",
    "Какая станция стала одной из первых открытых станций метро в 1935 году?": "Sokolniki Moscow Metro",
    "На какой станции установлены 32 витража с подсветкой изнутри?": "Novoslobodskaya Moscow Metro",
    "Какая станция метро считается самой красивой и часто называется «подземным дворцом»?": "Mayakovskaya Moscow Metro",
    "На какой станции находится самый длинный эскалатор в московском метро?": "Park Pobedy Moscow Metro escalator",
    # строительная техника — поиск по ответу (названию техники на английском)
    "Экскаватор": "excavator construction",
    "Бетономешалка": "concrete mixer truck",
    "Башенный кран": "tower crane construction",
    "Бульдозер": "bulldozer construction",
    "Каток": "road roller construction",
    "Автокран": "mobile crane truck",
    "Бетононасос": "concrete pump truck",
}


def build_search_term(q):
    """Определяем, по какому запросу искать фото для вопроса."""
    if q["question"] in SEARCH_TERMS:
        return SEARCH_TERMS[q["question"]]
    if q.get("answer") in SEARCH_TERMS:
        return SEARCH_TERMS[q["answer"]]
    return q["question"]


def search_photo(search_term):
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": search_term,
        "srnamespace": 6,
        "srlimit": 5,
    }
    headers = {
        "User-Agent": "MetroQuizBot/1.0 (educational project)"
    }
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"  ! Ошибка запроса: {e}")
        return None

    results = data.get("query", {}).get("search", [])
    for item in results:
        title = item["title"]
        if not title.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        filename = title.replace("File:", "")
      return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(filename)}?width=800"
    return None


def process_file(path):
    print(f"\n=== {path.name} ===")
    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    for q in questions:
        term = build_search_term(q)
        print(f"Ищу фото для: {term}...")
        url = search_photo(term)
        q["photo_url"] = url
        print(f"  -> {url}")
        time.sleep(3.0)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)


def main():
    for path in sorted(QUIZZES_DIR.glob("*.json")):
        process_file(path)
    print("\nГотово! Все викторины обновлены.")


if __name__ == "__main__":
    main()