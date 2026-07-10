# PulseFeed

A personalized news aggregator web application that delivers news based on user
interests, categories, and preferences. Built with Flask, NewsData.io
integration, and a clean, user-friendly interface.

## Features

- User registration & login
- Personalized feed based on categories, sources, and countries
- Save articles to read later (bookmark feature)
- Search across live and saved articles
- News result caching to reduce API calls

## Tech Stack

- **Backend:** Flask (Python), Flask-Login, Flask-SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript (Bootstrap)
- **Database:** PostgreSQL (Neon) in production; SQLite fallback for local dev
- **APIs:** NewsData.io (for live news data)
- **Server:** Gunicorn (production)

## Project Structure

```
PulseFeed/
├── pulsefeed/
│   ├── __init__.py          # App factory (create_app), extension init
│   ├── config.py            # Config class reading from env vars
│   ├── models.py            # User, UserPreference, SavedArticle, CachedArticle
│   ├── routes/
│   │   ├── __init__.py      # Blueprint definitions
│   │   ├── auth.py          # login, register, logout
│   │   ├── news.py          # index, get_news, search_news
│   │   ├── preferences.py   # set_preferences
│   │   ├── saved.py         # saved, save_article, get_saved_articles
│   │   └── health.py        # /health endpoint
│   ├── services/
│   │   └── news_service.py  # NewsData.io fetching, caching, normalization
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, images
├── run.py                   # Entry point
├── requirements.txt
├── .env.example             # Template for environment variables
└── README.md
```

## Installation & Setup

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values (see below).

Run the app (development):

```bash
python run.py
```

Run with Gunicorn (production):

```bash
gunicorn run:app
```

## Required Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Flask session signing key. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` | (random 64-char hex) |
| `NEWSDATA_API_KEY` | API key from [newsdata.io](https://newsdata.io) | `pub_...` |
| `DATABASE_URL` | Neon Postgres connection string (must include `?sslmode=require`) | `postgresql://user:pass@host/db?sslmode=require` |

### Optional Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SQLALCHEMY_DATABASE_URI` | (falls back to `DATABASE_URL` or `sqlite:///database.db`) | Direct SQLAlchemy URI override |
| `NEWS_CACHE_TTL` | `600` | News cache time-to-live in seconds (10 min) |
| `NEWSDATA_TIMEOUT` | `15` | NewsData.io request timeout in seconds |
| `FLASK_ENV` | `production` | Set to `development` to enable debug mode |

## Health Check

`GET /health` returns `200 {"status": "ok", "database": "connected"}` when the
app and database are healthy. Use this for Render or other platform health
checks.
