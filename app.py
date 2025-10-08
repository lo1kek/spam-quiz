import csv
import json
import os
import sqlite3
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, List, Tuple

from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "spam_quiz.db"
CONFIG_PATH = BASE_DIR / "config.json"
ENV_PATH = BASE_DIR / ".env"


def load_env(path: Path) -> None:
    """Populate os.environ with variables from a simple .env file."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key and key not in os.environ:
            os.environ[key] = value


load_env(ENV_PATH)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            correct_answers INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            image_name TEXT NOT NULL,
            user_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            FOREIGN KEY(result_id) REFERENCES results(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


def load_config() -> List[Dict[str, str]]:
    if not CONFIG_PATH.exists():
        return []
    with CONFIG_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_config(items: List[Dict[str, str]]) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def validate_phone(phone: str) -> bool:
    return phone.startswith("+7") and len(phone) == 12 and phone[1:].isdigit()


def ensure_user_session() -> Tuple[Dict[str, str], Dict[str, object]]:
    user = session.get("user")
    quiz = session.get("quiz")
    if not user or not quiz:
        raise PermissionError
    return user, quiz


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", error=None)


@app.route("/start", methods=["POST"])
def start_quiz():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()

    error = None
    if not name:
        error = "Введите имя"
    elif not validate_phone(phone):
        error = "Введите номер в формате +7XXXXXXXXXX"

    if error:
        return render_template("index.html", error=error)

    config = load_config()
    if not config:
        error = "Нет доступных карточек для викторины. Обратитесь к администратору."
        return render_template("index.html", error=error)

    session["user"] = {"name": name, "phone": phone}
    session["quiz"] = {
        "current_index": 0,
        "correct": 0,
        "answers": [],
        "total": len(config),
    }
    session.pop("result_saved", None)
    return redirect(url_for("quiz"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    try:
        user, quiz_state = ensure_user_session()
    except PermissionError:
        return redirect(url_for("index"))

    config = load_config()
    total = len(config)
    if total == 0:
        session.pop("quiz", None)
        return redirect(url_for("index"))

    current_index = quiz_state.get("current_index", 0)
    if request.method == "POST":
        answer = request.form.get("answer")
        if current_index < total and answer in {"spam", "not_spam"}:
            item = config[current_index]
            is_correct = 1 if answer == item.get("correct") else 0
            quiz_state["answers"].append(
                {
                    "filename": item.get("filename"),
                    "user_answer": answer,
                    "is_correct": bool(is_correct),
                }
            )
            if is_correct:
                quiz_state["correct"] = quiz_state.get("correct", 0) + 1
            quiz_state["current_index"] = current_index + 1
            session["quiz"] = quiz_state
        if quiz_state["current_index"] >= total:
            return redirect(url_for("result"))
        return redirect(url_for("quiz"))

    if current_index >= total:
        return redirect(url_for("result"))

    image = config[current_index]
    return render_template(
        "quiz.html",
        image=image,
        current_index=current_index,
        total=total,
        user=user,
    )


@app.route("/result", methods=["GET"])
def result():
    try:
        user, quiz_state = ensure_user_session()
    except PermissionError:
        return redirect(url_for("index"))

    correct = quiz_state.get("correct", 0)
    total = quiz_state.get("total", 0)

    if not session.get("result_saved"):
        result_id = store_result(user, quiz_state)
        session["result_id"] = result_id
        session["result_saved"] = True

    return render_template(
        "result.html",
        name=user.get("name"),
        correct=correct,
        total=total,
        detailed=quiz_state.get("answers", []),
    )


@app.post("/restart")
def restart():
    session.pop("user", None)
    session.pop("quiz", None)
    session.pop("result_id", None)
    session.pop("result_saved", None)
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("admin_logged_in"):
        return render_admin_dashboard()

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        error = "Неверный логин или пароль"

    return render_template("admin_login.html", error=error)


@app.post("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin"))


@app.post("/admin/config")
def update_config():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    form_items = request.form
    config = load_config()
    updated: List[Dict[str, str]] = []
    index = 0
    while True:
        filename_key = f"filename_{index}"
        answer_key = f"config_{index}"
        if filename_key not in form_items:
            break
        filename = form_items.get(filename_key)
        correct_value = form_items.get(answer_key, "not_spam")
        updated.append({"filename": filename, "correct": correct_value})
        index += 1

    if updated:
        save_config(updated)

    return redirect(url_for("admin"))


@app.get("/admin/export")
def export_results():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, phone, correct_answers, total_questions, created_at FROM results ORDER BY datetime(created_at) DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    def generate():
        header = ["name", "phone", "correct_answers", "total_questions", "created_at"]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(header)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        for row in rows:
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = f"spam_quiz_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def render_admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, phone, correct_answers, total_questions, created_at FROM results ORDER BY datetime(created_at) DESC"
    )
    results = cursor.fetchall()
    conn.close()

    config = load_config()

    return render_template(
        "admin_dashboard.html",
        results=results,
        config=config,
    )


def store_result(user: Dict[str, str], quiz_state: Dict[str, object]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO results (name, phone, correct_answers, total_questions, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user.get("name"),
            user.get("phone"),
            quiz_state.get("correct", 0),
            quiz_state.get("total", 0),
            datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    result_id = cursor.lastrowid

    answers: List[Dict[str, object]] = quiz_state.get("answers", [])
    cursor.executemany(
        """
        INSERT INTO answers (result_id, image_name, user_answer, is_correct)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                result_id,
                answer.get("filename"),
                answer.get("user_answer"),
                1 if answer.get("is_correct") else 0,
            )
            for answer in answers
        ],
    )
    conn.commit()
    conn.close()
    return result_id


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
