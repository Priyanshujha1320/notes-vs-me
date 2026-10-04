from __future__ import annotations
"""End-to-end pipeline test with the model mocked out.

Verifies ingest -> store -> sampling -> question generation -> grading ->
stats without needing Ollama. Run: .venv/bin/python scripts/test_pipeline.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import ingest, llm, quiz, store  # noqa: E402

# --- isolate the database ---------------------------------------------------
store.DB_PATH = Path(tempfile.mkdtemp()) / "test.db"
store.init()

# --- mock the model ----------------------------------------------------------
QUESTION_JSON = json.dumps({
    "topic": "Calvin cycle",
    "type": "short",
    "question": "Where does the Calvin cycle take place, and what does it use?",
    "options": None,
    "answer": "In the stroma, using ATP and NADPH from the light-dependent reactions.",
    "explanation": "Space matters: thylakoid = light, stroma = Calvin cycle.",
})
MCQ_JSON = json.dumps({
    "topic": "Limiting factors",
    "type": "mcq",
    "question": "Which enzyme catalyses the fixation of CO2 in the Calvin cycle?",
    "options": ["RuBisCO", "ATP synthase", "Amylase", "NADP reductase"],
    "answer": "RuBisCO",
    "explanation": "RuBisCO joins CO2 to RuBP — the most abundant enzyme on Earth.",
})
GRADE_JSON = json.dumps({"correct": True, "feedback": "Good — you named the place and the inputs."})
llm.chat = lambda _p, _s="", json_mode=False: (QUESTION_JSON if "short-answer" in _p
                                               else MCQ_JSON if "excerpt" in _p
                                               else GRADE_JSON)

# --- run the pipeline ----------------------------------------------------------
pdf_path = Path(__file__).resolve().parent.parent / "sample-notes.pdf"
assert pdf_path.exists(), "run scripts/make_demo_pdf.py first"
text = ingest.extract_text(pdf_path.read_bytes())
chunks = ingest.chunk_text(text)
assert len(chunks) >= 3, f"chunking produced {len(chunks)} chunks"
print(f"1. ingest: {len(chunks)} chunks, first starts: {chunks[0][:60]!r}")

doc_id = store.add_document("sample-notes.pdf")
for i, c in enumerate(chunks):
    store.add_chunk(doc_id, i, c)
assert len(store.all_chunks()) == len(chunks)
print("2. store: chunks saved and retrievable")

import random
random.seed(1)  # deterministic mcq/short mix
questions = [quiz.generate_question(c) for c in store.all_chunks()[:3]]
assert all(q["type"] in ("mcq", "short") and q["topic"] for q in questions)
assert any(q["type"] == "mcq" and q["options"] for q in questions)
print(f"3. generation: {len(questions)} questions (mcq + short both work), "
      f"e.g. {questions[0]['question'][:50]!r}")

sq = next(q for q in questions if q["type"] == "short")
mq = next(q for q in questions if q["type"] == "mcq")
res = quiz.grade(store.get_question(sq["id"]), "In the stroma, using ATP and NADPH.")
assert res["correct"] is True, res
mcq_res = quiz.grade(store.get_question(mq["id"]), "RuBisCO")
assert mcq_res["correct"] is True
store.record_attempt(sq["id"], "In the stroma", True, res["feedback"])
store.record_attempt(mq["id"], "Amylase", False, mcq_res["feedback"])
print("4. grading + attempts: short (model) and mcq (deterministic) both graded")

topics = store.topic_stats()
assert topics and topics[0]["topic"] == "Calvin cycle"
overall = store.overall_stats()
assert overall["attempts"] == 2 and overall["correct"] == 1
print(f"5. stats: {overall}")

# sampling weights shouldn't crash with partial history
from app.main import _pick_chunks  # noqa: E402
picked = _pick_chunks(5)
assert len(picked) == min(5, len(store.all_chunks()))
print(f"6. sampling: picked {len(picked)} chunks weighted toward weak topics")

print("\nALL PIPELINE TESTS PASSED ✅")
