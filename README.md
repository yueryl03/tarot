# Tarot

A Rider-Waite-Smith reading app. One reading is one physical deck of 78 cards. The deck is shuffled once, stored, and revealed without replacement. Upright and reversed are orientations of a card, not extra cards. The language model never chooses the cards.

## Documents

| Document | What it covers |
| --- | --- |
| [Tarot drawing engine](TAROT_ENGINE_THEORY_EN.md) | Why the shuffle, orientations, and spreads use this probability model. |
| [Backend](backend/README.md) | API, database, local setup, tests, and limitations. |
| [Frontend](frontend/README.md) | The reading page and how it calls the API. |

## Run locally

Start PostgreSQL, then from `backend/`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

From `frontend/`:

```bash
npm install
npm run dev
```

Open http://localhost:3000. API docs are at http://localhost:8000/docs.
