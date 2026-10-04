# Notes vs. Me 📚⚔️

Turn your own course notes into an examiner that never gets tired of grilling you.
**Local-first: your notes never have to leave your laptop. No accounts, no
subscription.**

## Why

AI study apps want your notes uploaded to their servers. Your syllabus, your
past papers, your handwriting — all of it leaving your machine. **Notes vs. Me**
keeps the whole loop on your machine by default: an open-weight model (Gemma 3,
via [Ollama](https://ollama.com)) reads *your* PDFs, writes exam questions from
them, grades your answers, and shows you a heatmap of the topics you keep
failing. (If your laptop can't run a model, there's a hosted fallback — still
open weights, and the app tells you when it's on.)

It was built for a real friend who was revising from a folder of PDFs the night
before every exam, with no way to know which topics were actually shaky.

## How it works

```
PDF → text chunks (PyMuPDF, paragraph-aware)
                         ↓
        chunk sampling (weighted toward your weak topics)
                         ↓
        question generation (open-weight model)
                         ↓
        you answer → grading → feedback + weak-topic heatmap
```

- **Chunk sampling**: when you ask for a quiz, chunks are picked *weighted by
  your history* — untested material first, then the topics that keep beating
  you. All state lives in SQLite: one file on your disk, no vector database,
  no server.
- **Question generation**: the model writes an exam question per chunk as
  strict JSON: a topic label, the question, options, the answer, and an
  explanation a student would actually find useful.
- **Grading**: multiple-choice is graded deterministically; short answers are
  graded by the model against a model answer, strictly on understanding,
  generously on wording.

## The model: local first, hosted fallback

The app talks to **open-weight models only**, through one interface:

- **Local (default)**: [Ollama](https://ollama.com) running on your machine —
  Gemma 3 1B for questions — ~1GB of RAM, safe on an 8GB laptop. Offline, private, free forever.
- **Hosted fallback**: if your laptop can't run a model, set a free
  [Groq](https://console.groq.com) key and the app uses the same open weights
  (Llama 3.1) served by Groq. Still open models — just borrowed compute.

Selection is automatic: Ollama if it answers, hosted if a key exists, and a
clear banner if neither. You can pin one with `NVM_PROVIDER`.

## Run it

Requirements: Python 3.9+, plus either Ollama (local) or a free Groq key (hosted).

```bash
# local route (recommended):
ollama pull gemma3:1b

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app
```

Open http://localhost:8000, drop in a PDF, and get grilled.

For the hosted route instead, export a key and start the server — the app
picks Groq automatically when Ollama isn't running:

```bash
NVM_GROQ_API_KEY=gsk_... .venv/bin/uvicorn app.main:app
```

| Variable | Default | Meaning |
|---|---|---|
| `NVM_PROVIDER` | auto | `ollama` or `groq` |
| `NVM_CHAT_MODEL` | `gemma3:1b` | Local model; set `gemma3:4b` on 16GB+ machines |
| `NVM_OLLAMA_HOST` | `http://localhost:11434` | Where Ollama lives |
| `NVM_GROQ_API_KEY` | — | Groq key for the hosted fallback |
| `NVM_GROQ_MODEL` | `llama-3.1-8b-instant` | Open model served by Groq |

## Stack

| Layer | Choice | Why open |
|---|---|---|
| Generation | [Gemma 3](https://ai.google.dev/gemma) (1B default, 4B on roomier machines) via Ollama; Llama 3.1 via Groq as fallback | Open weights either way |
| Backend | FastAPI + SQLite | One `pip install`, one file of state |
| Frontend | Single HTML file, vanilla JS | No build step, no telemetry |

## Privacy, concretely

- **Local mode**: notes are parsed on your machine and sent only to
  `localhost:11434` — your own Ollama. Nothing else ever sees them.
- **Hosted fallback**: chunk text goes to Groq's API to be turned into
  questions. That's the one trade-off, and the app tells you which mode
  you're in. Your call, your data.
- `data/notes.db` holds every chunk, question and attempt. Delete it and the
  app forgets you entirely.
- Local mode works on a plane, in a hostel with dead Wi-Fi, during an
  exam-week blackout.

## License

MIT
