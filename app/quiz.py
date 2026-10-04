from __future__ import annotations
"""The grilling engine: turn a note chunk into a question, grade the answer.

Every call here hits the locally-running open model — this is the part of the
app that stops working without open-source AI, by design.
"""
import random

from . import llm, store

QUESTION_SYSTEM = (
    "You are a strict but fair examiner. You write exam questions from "
    "university course notes. You always reply with exactly one JSON object "
    "and nothing else."
)

QUESTION_PROMPT = """Here is an excerpt from a student's course notes:

---
{chunk}
---

Write ONE exam question that tests real understanding of this excerpt (not
trivia, not copying a sentence back). {type_instruction}

Give a SPECIFIC topic label naming the concept in this excerpt (e.g.
"RuBisCO and photorespiration" — not a whole-chapter word like "Photosynthesis").

Reply with JSON only. Here is a worked EXAMPLE of the exact shape and quality
expected — write your own, different question about the excerpt:

{{
  "topic": "Light-dependent reactions",
  "type": "mcq",
  "question": "Why is the splitting of water essential to the light-dependent reactions?",
  "options": ["It replaces the electrons lost by photosystem II", "It produces glucose directly", "It removes carbon dioxide from the stroma", "It regenerates RuBP"],
  "answer": "It replaces the electrons lost by photosystem II",
  "explanation": "Photolysis supplies photosystem II with fresh electrons and releases oxygen as a by-product."
}}

Rules:
- If writing an mcq: "options" must be four FULL answer texts — never single
  letters like "A", "B", "C", "D" — and "answer" must be one option copied
  verbatim.
- If writing a short question: set "options" to null and make "answer" a
  1-3 sentence model answer you would accept.
- If the instruction asks for multiple-choice, "type" must be "mcq"; if it
  asks for a short answer, "type" must be "short".
- The question must be answerable from the excerpt alone.
- Reply with the JSON object only, no commentary.
"""

MCQ_INSTRUCTION = "Make it a multiple-choice question with exactly 4 options, one correct, the others plausible but wrong."
SHORT_INSTRUCTION = "Make it a short-answer question that takes 1-3 sentences to answer."

GRADE_SYSTEM = (
    "You are an examiner grading a student's spoken answer against your "
    "model answer. Be strict about understanding, generous about wording. "
    "Reply with exactly one JSON object and nothing else."
)

GRADE_PROMPT = """Question: {question}

Model answer: {answer}

Student's answer: {given}

Grade the student's answer. Reply with JSON only:
{{
  "correct": true or false,
  "feedback": "one or two sentences: what they got right, and if wrong, what to review"
}}
"""


def _as_text(value) -> str:
    """Small models sometimes return a list where text was asked for."""
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value).strip()


def generate_question(chunk: dict) -> dict:
    """Turn one note chunk into a stored, structured question."""
    qtype = "mcq" if random.random() < 0.6 else "short"
    prompt = QUESTION_PROMPT.format(
        chunk=chunk["text"][:2000],
        type_instruction=MCQ_INSTRUCTION if qtype == "mcq" else SHORT_INSTRUCTION,
    )
    last_error = None
    for _ in range(3):
        try:
            data = llm.extract_json(llm.chat(prompt, QUESTION_SYSTEM, json_mode=True))
            topic = _as_text(data["topic"])
            question = _as_text(data["question"])
            answer = _as_text(data["answer"])
            explanation = _as_text(data["explanation"])
            raw_options = data.get("options")
            # the model may answer a different type than we asked for —
            # trust what it actually returned, coercing mcq -> short if the
            # options didn't come back usable
            qtype = data.get("type") if data.get("type") in ("mcq", "short") \
                else qtype
            if qtype == "mcq":
                if isinstance(raw_options, list) and len(raw_options) == 4 \
                        and answer in [str(o) for o in raw_options]:
                    options = [str(o) for o in raw_options]
                else:
                    qtype, options = "short", None
            else:
                options = None
            if not all([topic, question, answer, explanation]):
                raise ValueError("empty field")
            qid = store.save_question(chunk["id"], topic, qtype, question,
                                      options, answer, explanation)
            return {"id": qid, "topic": topic, "type": qtype,
                    "question": question, "options": options}
        except (KeyError, ValueError, llm.ModelDown) as e:
            last_error = e
            print(f"[quiz] attempt failed on chunk {chunk['id']}: {e!r}",
                  flush=True)
    raise RuntimeError(f"question generation failed after 3 tries: {last_error}")


def grade(question: dict, given: str) -> dict:
    """Grade an answer, strictly by hand for MCQ, by the model for short."""
    if question["type"] == "mcq":
        correct = given.strip() == question["answer"].strip()
        feedback = ("Correct! " if correct else "Not quite. ") \
            + question["explanation"]
        return {"correct": correct, "feedback": feedback}

    prompt = GRADE_PROMPT.format(question=question["prompt"],
                                 answer=question["answer"], given=given)
    for _ in range(2):
        try:
            data = llm.extract_json(llm.chat(prompt, GRADE_SYSTEM, json_mode=True))
            return {"correct": bool(data["correct"]),
                    "feedback": str(data["feedback"]).strip()}
        except (KeyError, ValueError, llm.ModelDown):
            continue
    # never block a student on a grading hiccup — hand them the model answer
    return {"correct": False,
            "feedback": f"(Grading hiccup — here's the model answer.) {question['answer']}"}
