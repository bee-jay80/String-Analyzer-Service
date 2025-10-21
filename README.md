# String Analyzer Service

Small Django service that analyzes strings and exposes a small REST API.

## What this repo contains

- `app/` — Django app with model, views and urls
- `docs/index.html` — simple HTML UI documentation
- `DOCS.md` — full API reference

## Quick install (local)

1. Create a Python virtual environment and activate it (example using python -m venv):

```bash
python -m venv venv
source venv/Scripts/activate  # on Windows (Git Bash) use: source venv/Scripts/activate
pip install -r requirements.txt
```

2. Run migrations and start the dev server:

```bash
python manage.py migrate
python manage.py runserver
```

3. Browse the API docs locally at:

```
docs/index.html
```

## Running tests

(Test runner to be added — add tests in `app/tests.py`.)

## Documentation

Detailed docs: `DOCS.md` and interactive UI at `docs/index.html`.

## Documentation

You can view the Live documentation UI at:

```
http://127.0.0.1:8000/docs/index.html
```

