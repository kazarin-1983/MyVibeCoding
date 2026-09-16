let quizQuestions = [];
let currentQuizId = null;
let currentRound = 1;
let totalRounds = 0;
let score = 0;
let currentQuestion = null;
let isAnswered = false;
let availableQuestions = [];
let answeredIds = [];
let finished = false;

// Элементы
const subtitle = document.getElementById("subtitle");
const quizPicker = document.getElementById("quiz-picker");
const gameBlock = document.getElementById("game");
const scoreElement = document.getElementById("score");
const roundElement = document.getElementById("round");
const totalRoundsElement = document.getElementById("total-rounds");
const questionText = document.getElementById("question-text");
const questionPhoto = document.getElementById("question-photo");
const optionsContainer = document.getElementById("options-container");
const messageElement = document.getElementById("message");
const nextButton = document.getElementById("next-btn");
const restartButton = document.getElementById("restart-btn");
const backButton = document.getElementById("back-btn");

function shuffle(arr) {
    return [...arr].sort(() => Math.random() - 0.5);
}

async function apiGet(url) {
    const r = await fetch(url, { credentials: "same-origin" });
    if (!r.ok) throw new Error(`GET ${url} → ${r.status}`);
    return r.json();
}

async function apiPost(url, body) {
    const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(body ?? {}),
    });
    if (!r.ok) throw new Error(`POST ${url} → ${r.status}`);
    return r.json();
}

async function saveProgress() {
    await apiPost(`/api/progress/${currentQuizId}`, {
        round: currentRound,
        score: score,
        answered_ids: answeredIds,
        finished: finished,
    });
}

// ─── Экран выбора викторины ─────────────────────────────

async function showQuizPicker() {
    quizPicker.innerHTML = "";
    gameBlock.style.display = "none";
    quizPicker.style.display = "flex";
    subtitle.textContent = "Выбери тему";

    try {
        const quizzes = await apiGet("/api/quizzes");
        quizzes.forEach(q => {
            const btn = document.createElement("button");
            btn.className = "quiz-choice";
            btn.textContent = q.title;
            btn.addEventListener("click", () => startQuiz(q.id, q.title));
            quizPicker.appendChild(btn);
        });
    } catch (e) {
        quizPicker.innerHTML = `<p>Ошибка загрузки тем: ${e.message}</p>`;
    }
}

// ─── Запуск конкретной викторины ────────────────────────

async function startQuiz(quizId, title) {
    // ← ИЗМЕНЕНО: запоминаем последнюю тему, чтобы пережить F5
    localStorage.setItem("lastQuizId", quizId);
    localStorage.setItem("lastQuizTitle", title);

    currentQuizId = quizId;
    quizPicker.style.display = "none";
    gameBlock.style.display = "flex";
    subtitle.textContent = title;

    // Сброс локального состояния перед загрузкой
    quizQuestions = [];
    currentRound = 1;
    score = 0;
    availableQuestions = [];
    answeredIds = [];
    finished = false;
    currentQuestion = null;

    try {
        const [questions, progress] = await Promise.all([
            apiGet(`/api/questions/${quizId}`),
            apiGet(`/api/progress/${quizId}`),
        ]);

        quizQuestions = questions;
        totalRounds = quizQuestions.length;

        currentRound = progress.round || 1;
        score = progress.score || 0;
        answeredIds = progress.answered_ids || [];
        finished = progress.finished || false;

        availableQuestions = quizQuestions.filter(
            q => !answeredIds.includes(q.id)
        );

        roundElement.textContent = currentRound;
        totalRoundsElement.textContent = totalRounds;
        scoreElement.textContent = score;
        nextButton.style.display = "block";

        if (finished || availableQuestions.length === 0) {
            showResults();
            return;
        }
        startRound();
    } catch (e) {
        questionText.textContent = "Ошибка загрузки 😢";
        messageElement.textContent = e.message;
        console.error(e);
    }
}

// ─── Игровая логика ─────────────────────────────────────

function startRound() {
    isAnswered = false;
    nextButton.disabled = true;
    nextButton.textContent =
        currentRound === totalRounds ? "Завершить игру" : "Следующий вопрос";
    messageElement.textContent = "Выбери вариант ответа";
    messageElement.style.color = "#475569";

    if (availableQuestions.length === 0) {
        showResults();
        return;
    }

    const randomIndex = Math.floor(Math.random() * availableQuestions.length);
    currentQuestion = availableQuestions.splice(randomIndex, 1)[0];

    questionText.textContent = currentQuestion.question;

    questionPhoto.removeAttribute("src");
    questionPhoto.classList.remove("visible");
    if (currentQuestion.photo_url) {
        questionPhoto.src = currentQuestion.photo_url;
        questionPhoto.alt = currentQuestion.answer;
        questionPhoto.classList.add("visible");
    }

    const wrongAnswers = currentQuestion.options.filter(
        opt => opt !== currentQuestion.answer
    );
    const roundChoices = shuffle([
        currentQuestion.answer,
        ...shuffle(wrongAnswers).slice(0, 3),
    ]);

    optionsContainer.innerHTML = "";
    roundChoices.forEach(choice => {
        const btn = document.createElement("button");
        btn.className = "btn-option";
        btn.textContent = choice;
        btn.addEventListener("click", () => handleChoice(choice, btn));
        optionsContainer.appendChild(btn);
    });

    roundElement.textContent = currentRound;
    scoreElement.textContent = score;
}

async function handleChoice(selected, clickedBtn) {
    if (isAnswered) return;
    isAnswered = true;

    const allButtons = optionsContainer.querySelectorAll(".btn-option");
    allButtons.forEach(btn => {
        btn.disabled = true;
        if (btn.textContent === currentQuestion.answer) {
            btn.classList.add("correct");
        }
    });

    if (selected === currentQuestion.answer) {
        score++;
        scoreElement.textContent = score;
        messageElement.textContent = "Верно! 🎉";
        messageElement.style.color = "#10b981";
    } else {
        clickedBtn.classList.add("wrong");
        messageElement.textContent = `Мимо! Правильный ответ: ${currentQuestion.answer} 🧐`;
        messageElement.style.color = "#ef4444";
    }

    answeredIds.push(currentQuestion.id);
    nextButton.disabled = false;

    try {
        await saveProgress();
    } catch (e) {
        console.error("Не удалось сохранить прогресс:", e);
    }
}

nextButton.addEventListener("click", async () => {
    if (currentRound < totalRounds && availableQuestions.length > 0) {
        currentRound++;
        await saveProgress();
        startRound();
    } else {
        finished = true;
        await saveProgress();
        showResults();
    }
});

function showResults() {
    optionsContainer.innerHTML = "";
    questionPhoto.classList.remove("visible");
    questionPhoto.removeAttribute("src");
    questionText.textContent = `🏆 Игра окончена! Твой счет: ${score} из ${totalRounds}`;
    messageElement.textContent = "Нажми «Заново» или выбери другую тему";
    messageElement.style.color = "#ea580c";
    nextButton.style.display = "none";
}

// ─── Кнопки ──────────────────────────────────────────────

restartButton.addEventListener("click", async () => {
    try {
        await apiPost(`/api/reset/${currentQuizId}`);
    } catch (e) {
        console.error("Не удалось сбросить прогресс:", e);
    }
    startQuiz(currentQuizId, subtitle.textContent);
});

// ← ИЗМЕНЕНО: при смене темы забываем последнюю, чтобы F5 не возвращал в игру
backButton.addEventListener("click", () => {
    localStorage.removeItem("lastQuizId");
    localStorage.removeItem("lastQuizTitle");
    showQuizPicker();
});

// ─── Точка входа ─────────────────────────────────────────
// ← ИЗМЕНЕНО: вместо безусловного showQuizPicker() —
// проверяем, была ли открыта тема, и восстанавливаем её.

const lastQuizId = localStorage.getItem("lastQuizId");
const lastQuizTitle = localStorage.getItem("lastQuizTitle");

if (lastQuizId && lastQuizTitle) {
    startQuiz(lastQuizId, lastQuizTitle);
} else {
    showQuizPicker();
}