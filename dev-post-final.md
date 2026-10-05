# I built an AI examiner that reads my friend's notes — without the notes ever leaving their laptop

## What I built, and who it's for

**[Notes vs. Me](https://github.com/Priyanshujha1320/notes-vs-me)** is a study app with one job: take the PDFs a
student already has — syllabus, lecture slides, past papers — and turn them
into an examiner that grills them, question after question, then shows exactly
which topics they keep failing.

I built it for a friend doing their undergrad who does the thing every student
does: reads the notes three times, feels prepared, walks into the exam, and
discovers that *reading* and *being asked* are completely different skills.
They had notes. They had questions at the back of the textbook. What they
didn't have was something that looked at *their* notes and asked *them* the
awkward follow-up.

And here's the constraint that shaped the whole build: their laptop is
where the notes live, where the revision happens, and — crucially — where the
notes should stay. No student wants their past papers uploaded to somebody's
cloud to "personalise their learning". So the default mode runs the entire AI
loop on their machine, and it all works offline.

## Demo

- **Live landing page**: [priyanshujha1320.github.io/notes-vs-me](https://priyanshujha1320.github.io/notes-vs-me/)
- **Full app** (needs Ollama + a laptop): clone, `ollama pull gemma3:1b`, `pip install -r requirements.txt`, run — ten minutes
- **The hero**: a seeded 3D flow field where some particles periodically loop back along their own trails — spaced repetition, made visible

## The code

[github.com/Priyanshujha1320/notes-vs-me](https://github.com/Priyanshujha1320/notes-vs-me) — MIT licensed. FastAPI + SQLite + a single-file
vanilla-JS frontend — no build step, nothing to trust. Six commits, one
weekend.

## How I built it

The pipeline is deliberately boring — boring is what survives exam week:

1. **Ingest** — a PDF is parsed with PyMuPDF into ~1200-character,
   paragraph-aware chunks.
2. **Sample** — when you ask for a quiz, chunks are picked *weighted by your
   history*: material you've never been tested on first, then the topics you
   keep failing. All state lives in SQLite — one file on the student's disk.
   No vector database, no server, no account.
3. **Generate** — Gemma 3 (open weights, via Ollama) writes an exam question
   per chunk as strict JSON: a topic label, the question, options, the
   answer, and an explanation a student would actually find useful.
4. **Grade** — MCQs are graded deterministically. Short answers are graded by
   the same model against a model answer, with instructions to be strict about
   understanding and generous about wording. When grading hiccups, the app
   falls back to showing the model answer rather than blocking the student.

The fun part was the sampling loop. A static quiz generator gets boring in
about a day; a griller that remembers you failed "Calvin cycle" twice and
quietly schedules it for next round behaves like something that *wants* you to
pass. That loop is about ten lines around a weighted shuffle.

The not-fun part was coaxing a 1B-parameter model into reliable JSON. Small
open models copy your prompt's placeholder literally — mine happily returned
`"options": ["A", "B", "C", "D"]`, letter options and all. The fix was a
worked example in the prompt (show, don't describe) plus a coercion layer
that trusts the model's actual answer type instead of fighting it. That's a
trade you make with small local models, and it's worth it: the whole AI stack
fits in about 1GB of RAM, so it runs on the kind of laptop students actually
own. If a machine can't run a model at all, there's a fallback to the same
open weights served by Groq — the app tells you, in plain words, which mode
you're in.

## Why open matters here (not just "open is nice")

- **It runs where the data lives.** Closed study APIs require the notes to be
  uploaded. Open weights on Ollama mean the entire loop — parse, generate,
  grade — happens on a laptop that may never see fast Wi-Fi during exam week.
- **Zero marginal cost matters for students.** A closed API costs money every
  time a student fails a question. Failing questions is *the point*. Gemma 3
  on Ollama costs nothing per query, so the app can be ruthless.
- **It can be forked for a different syllabus.** A medical student can swap
  the prompts for OSCE-style viva questions; a law student for case-law
  problem questions. Nothing about their revision is locked to my server, my
  pricing, or my roadmap.
- **It survives abandonment.** If I never touch this repo again, it keeps
  working. No shutdown notice turns a study tool into a brick.

## Handing it over

I'm handing the app to my friend this week with their own syllabus loaded —
watching a real student take the first grill is the whole point of this
build, and I'll update this section with what actually happens. My money is
on it finding the one section they skipped.

## What's next

- Photo-of-handwriting ingestion (local OCR — harder than it sounds on a laptop)
- A "grill me out loud" mode with open speech models
- Export of the weak-topic heatmap as a revision checklist

Try it on your own notes: [github.com/Priyanshujha1320/notes-vs-me](https://github.com/Priyanshujha1320/notes-vs-me). If it exposes a topic you were sure you
knew, that's the app working.

---

*Built for the [DEV Hacktoberfest Weekend Challenge](https://dev.to/devteam/join-the-hacktoberfest-weekend-challenge-build-for-a-friend-2450-in-prizes-across-17-winners-1aj5): open
source AI that solves a real problem for someone you love.*
