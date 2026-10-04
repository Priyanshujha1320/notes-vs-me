from __future__ import annotations
"""SQLite storage. No server, no account — one file on the student's disk."""
import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "notes.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    added_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id),
    idx INTEGER NOT NULL,
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    chunk_id INTEGER NOT NULL REFERENCES chunks(id),
    topic TEXT NOT NULL,
    type TEXT NOT NULL,             -- 'mcq' | 'short'
    prompt TEXT NOT NULL,
    options TEXT,                   -- JSON list, mcq only
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    given TEXT NOT NULL,
    correct INTEGER NOT NULL,
    feedback TEXT NOT NULL,
    answered_at TEXT NOT NULL
);
"""


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with db() as conn:
        conn.executescript(SCHEMA)


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


# --- documents & chunks ---------------------------------------------------

def add_document(name: str) -> int:
    with db() as conn:
        cur = conn.execute("INSERT INTO documents(name, added_at) VALUES(?,?)",
                           (name, now()))
        return cur.lastrowid


def add_chunk(doc_id: int, idx: int, text: str) -> int:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO chunks(doc_id, idx, text) VALUES(?,?,?)",
            (doc_id, idx, text))
        return cur.lastrowid


def list_documents() -> list[dict]:
    with db() as conn:
        rows = conn.execute(
            """SELECT d.*, COUNT(c.id) AS chunk_count
               FROM documents d LEFT JOIN chunks c ON c.doc_id = d.id
               GROUP BY d.id ORDER BY d.id DESC""").fetchall()
        return [dict(r) for r in rows]


def all_chunks() -> list[dict]:
    with db() as conn:
        rows = conn.execute(
            """SELECT c.*, d.name AS doc_name FROM chunks c
               JOIN documents d ON d.id = c.doc_id""").fetchall()
        return [dict(r) for r in rows]


def delete_document(doc_id: int) -> None:
    with db() as conn:
        conn.execute(
            """DELETE FROM questions WHERE chunk_id IN
               (SELECT id FROM chunks WHERE doc_id = ?)""", (doc_id,))
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))


# --- questions & attempts ---------------------------------------------------

def save_question(chunk_id: int, topic: str, qtype: str, prompt: str,
                  options: list[str] | None, answer: str,
                  explanation: str) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO questions
               (chunk_id, topic, type, prompt, options, answer, explanation)
               VALUES(?,?,?,?,?,?,?)""",
            (chunk_id, topic, qtype, prompt,
             json.dumps(options) if options else None,
             answer, explanation))
        return cur.lastrowid


def get_question(qid: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            """SELECT q.*, c.text AS source FROM questions q
               JOIN chunks c ON c.id = q.chunk_id WHERE q.id = ?""",
            (qid,)).fetchone()
        if row is None:
            return None
        q = dict(row)
        q["options"] = json.loads(q["options"]) if q["options"] else None
        return q


def record_attempt(question_id: int, given: str, correct: bool,
                   feedback: str) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO attempts(question_id, given, correct, feedback,
                                    answered_at)
               VALUES(?,?,?,?,?)""",
            (question_id, given, int(correct), feedback, now()))


def topic_stats() -> list[dict]:
    """Per-topic accuracy for the heatmap."""
    with db() as conn:
        rows = conn.execute(
            """SELECT q.topic,
                      COUNT(a.id) AS attempts,
                      SUM(a.correct) AS correct
               FROM questions q
               LEFT JOIN attempts a ON a.question_id = q.id
               GROUP BY q.topic
               ORDER BY attempts DESC, q.topic""").fetchall()
        out = []
        for r in rows:
            attempts, correct = r["attempts"] or 0, r["correct"] or 0
            out.append({
                "topic": r["topic"],
                "attempts": attempts,
                "correct": correct,
                "accuracy": round(correct / attempts * 100) if attempts else None,
            })
        return out


def overall_stats() -> dict:
    with db() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS attempts, SUM(correct) AS correct
               FROM attempts""").fetchone()
        attempts, correct = row["attempts"] or 0, row["correct"] or 0
        questions = conn.execute(
            "SELECT COUNT(*) AS c FROM questions").fetchone()["c"]
        return {
            "attempts": attempts,
            "correct": correct,
            "accuracy": round(correct / attempts * 100) if attempts else None,
            "questions": questions,
        }
