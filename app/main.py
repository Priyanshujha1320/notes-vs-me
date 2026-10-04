from __future__ import annotations
"""Notes vs. Me — the local study griller.

FastAPI app: upload PDFs, get grilled, watch your weak topics light up.
Run:  uvicorn app.main:app --reload   (from the project root)
"""
from pathlib import Path

import random
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import ingest, llm, quiz, store

app = FastAPI(title="Notes vs. Me")
store.init()

BASE_DIR = Path(__file__).resolve().parent.parent


# --- health ----------------------------------------------------------------

@app.get("/api/health")
def health():
    return llm.status()


# --- library ----------------------------------------------------------------

@app.post("/api/upload")
async def upload(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "PDFs only for now")
    pdf = await file.read()
    text = ingest.extract_text(pdf)
    chunks = ingest.chunk_text(text)
    if not chunks:
        raise HTTPException(400, "No readable text found in that PDF")
    doc_id = store.add_document(file.filename)
    for idx, chunk in enumerate(chunks):
        store.add_chunk(doc_id, idx, chunk)
    return {"document": file.filename, "chunks": len(chunks)}


@app.get("/api/documents")
def documents():
    return store.list_documents()


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int):
    store.delete_document(doc_id)
    return {"ok": True}


# --- quiz -------------------------------------------------------------------

def _pick_chunks(count: int) -> list[dict]:
    """Weight chunk sampling toward weak topics and untested material."""
    chunks = store.all_chunks()
    if not chunks:
        raise HTTPException(400, "Upload some notes first")
    stats = {s["topic"]: s for s in store.topic_stats()}

    # which chunks have been asked already, and how badly they went
    with store.db() as conn:
        rows = conn.execute(
            """SELECT q.chunk_id, q.topic, SUM(a.correct) AS correct,
                      COUNT(a.id) AS n
               FROM questions q LEFT JOIN attempts a ON a.question_id = q.id
               GROUP BY q.chunk_id""").fetchall()
    history = {r["chunk_id"]: dict(r) for r in rows}

    def weight(c: dict) -> float:
        h = history.get(c["id"])
        if h is None:
            return 3.0  # never asked: highest priority
        acc = (h["correct"] or 0) / h["n"] if h["n"] else 1.0
        return 1.0 + 2.0 * (1.0 - acc)  # struggle more -> get grilled more

    # weighted shuffle: high-weight chunks come first, all unique
    order = sorted(chunks, key=lambda c: -weight(c) * random.random())
    return order[:min(count, len(chunks))]


@app.post("/api/quiz/next")
def next_questions(count: int = 5):
    questions = []
    for chunk in _pick_chunks(count):
        try:
            questions.append(quiz.generate_question(chunk))
        except (llm.ModelDown, RuntimeError):
            if not questions:
                raise HTTPException(503, "The local model isn't responding")
            break  # partial quiz beats no quiz
    return questions


@app.post("/api/answer/{question_id}")
def answer(question_id: int, body: dict):
    q = store.get_question(question_id)
    if q is None:
        raise HTTPException(404, "No such question")
    given = str(body.get("answer", "")).strip()
    if not given:
        raise HTTPException(400, "Empty answer")
    result = quiz.grade(q, given)
    store.record_attempt(question_id, given, result["correct"],
                         result["feedback"])
    return result


# --- progress ----------------------------------------------------------------

@app.get("/api/stats")
def stats():
    return {"overall": store.overall_stats(), "topics": store.topic_stats()}


# --- static frontend ---------------------------------------------------------

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")
