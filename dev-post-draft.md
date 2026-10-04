# DEV post draft — Notes vs. Me

> Fill the `{placeholders}` before publishing. Writing quality is the heaviest
> judging criterion here — the draft below is written to be told as *your*
> story, so edit it until it sounds like you.

---

# I built an AI examiner that reads my friend's notes — without her notes ever leaving her laptop

## What I built, and who it's for

**[Notes vs. Me](REPO_LINK)** is a study app with one job: take the PDFs a
student already has — syllabus, lecture slides, past papers — and turn them
into an examiner that grills them, question after question, then shows exactly
which topics they keep failing.

I built it for {friend}, a {year} student who does the thing every student
does: reads the notes three times, feels prepared, walks into the exam, and
discovers that *reading* and *being asked* are completely different skills.
They had notes. They had questions at the back of the textbook. What they
didn't have was something that looked at *their* notes and asked *them* the
awkward follow-up.

And here's the constraint that shaped the whole build: {friend}'s laptop is
where the notes live, where the revision happens, and — crucially — where the
notes should stay. No student wants their past papers uploaded to somebody's
cloud to "personalise their learning". So the default mode runs the entire AI
loop on their machine, and it all works offline.

## Demo

- {Deployed link or Loom/YouTube demo video}
- {GIF/screenshot of a quiz round + the weak-topic heatmap}

## The code

{Repo link} — MIT licensed. It's a FastAPI app with a single-file vanilla-JS
frontend — no build step, nothing to trust. If you have
[Ollama](https://ollama.com), you can be grilling yourself within ten minutes:
`ollama pull gemma3:1b`, clone, `pip install`, run, drop a PDF.

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
own. If your machine can't run a model at all, there's a fallback to the same
open weights served by Groq — the app tells you, in plain words, which mode
you're in.

## Why open matters here (not just "open is nice")

This project only works because the pieces are open, and I mean that literally:

- **It runs where the data lives.** Closed study APIs require the notes to be
  uploaded. Open weights on Ollama mean the entire loop — parse, generate,
  grade — happens on a laptop that may never see fast Wi-Fi during exam week.
- **Zero marginal cost matters for students.** A closed API costs money every
  time a student fails a question. Failing questions is *the point*. Gemma 3
  on Ollama costs nothing per query, so the app can be ruthless.
- **It can be forked for a different syllabus.** A medical student can swap
  the prompts for OSCE-style viva questions; a law student for case-law
  problem questions. The models, the code and the data format are all open —
  nothing about their revision is locked to my server, my pricing, or my
  roadmap.
- **It survives abandonment.** If I never touch this repo again, it keeps
  working. No shutdown notice turns {friend}'s study tool into a brick.

## Handing it over

{The hand-over moment: how you gave it to them, what they said, what surprised
you. Honest beats polished — "it asked me about the one section I'd skipped"
is worth more than any feature list.}

## What's next

- Photo-of-handwriting ingestion (local OCR — harder than it sounds on a laptop)
- A "grill me out loud" mode with open speech models
- Export of the weak-topic heatmap as a revision checklist

Try it on your own notes: {repo link}. If it exposes a topic you were sure you
knew, that's the app working.

---

*Built for the [DEV Hacktoberfest Weekend Challenge](CHALLENGE_LINK): open
source AI that solves a real problem for someone you love. Prize categories:
Overall, Best Use of Gemma.*
