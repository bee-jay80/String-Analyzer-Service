# String Analyzer Service — API Documentation

This document provides detailed API reference for the String Analyzer Service. See also the UI at `docs/index.html` for a quick, styled view.

## Base URL

Assuming local development:

```
http://127.0.0.1:8000/
```

---

## 1) Create analyzed string

- Endpoint: POST `/strings/`
- Request body: application/json

Example request:

```json
{ "value": "string to analyze" }
```

Success response (201 Created):

```json
{
  "id": "sha256_hash_value",
  "value": "string to analyze",
  "properties": {
    "length": 16,
    "is_palindrome": false,
    "unique_characters": 12,
    "word_count": 3,
    "sha256_hash": "abc123...",
    "character_frequency_map": {
      "s": 2,
      "t": 3,
      "r": 2
    }
  },
  "created_at": "2025-08-27T10:00:00Z"
}
```

Errors:

- 400 Bad Request — missing or malformed body
- 409 Conflict — string already exists
- 422 Unprocessable Entity — wrong data type for `value`

---

## 2) Retrieve specific string

- Endpoint: GET `/strings/{string_value}/`
- The `{string_value}` is the raw string value (URL-encoded).

Success response: same shape as create response (200 OK)

Errors:

- 404 Not Found — string does not exist

---

## 3) List strings with filters

- Endpoint: GET `/strings/`
- Query parameters supported:
  - `is_palindrome` (true|false)
  - `min_length` (integer, inclusive)
  - `max_length` (integer, inclusive)
  - `word_count` (integer)
  - `contains_character` (single character)

Example:

```
GET /strings/?is_palindrome=true&min_length=5&max_length=20&word_count=2&contains_character=a
```

Success response (200 OK):

```json
{
  "data": [ /* array of items */ ],
  "count": 15,
  "filters_applied": { /* the query params as sent */ }
}
```

Errors:

- 400 Bad Request — invalid query parameter values/types

---

## 4) Natural language filtering

- Endpoint: GET `/strings/filter-by-natural-language/?query=...`
- The service uses small heuristics to map example phrases to filters.

Supported patterns (examples):

- "all single word palindromic strings" → `word_count=1`, `is_palindrome=true`
- "strings longer than 10 characters" → `min_length=11`
- "palindromic strings that contain the first vowel" → `is_palindrome=true`, `contains_character=a` (heuristic)
- "strings containing the letter z" → `contains_character=z`

Errors:

- 400 Bad Request — unable to parse the natural-language query or missing `query`
- 422 Unprocessable Entity — parsed but conflicting filters (e.g., min_length > max_length)

---

## 5) Delete a string

- Endpoint: DELETE `/strings/{string_value}/`
- Response: 204 No Content on success
- Errors: 404 Not Found if not present

---

## Test Examples (curl)

Create:

```bash
curl -X POST http://127.0.0.1:8000/strings/ \
  -H "Content-Type: application/json" \
  -d '{"value":"racecar"}'
```

List with filters:

```bash
curl "http://127.0.0.1:8000/strings/?is_palindrome=true&min_length=5"
```

Natural language:

```bash
curl "http://127.0.0.1:8000/strings/filter-by-natural-language/?query=all%20single%20word%20palindromic%20strings"
```

---

## Notes & migration

- The model uses a SHA-256 hex digest as the primary key (`id`). Creating the same `value` twice will conflict and return 409. If you need multiple identical values stored, you'll need to change the PK.
- If the model or field types change, add Django migrations. If you already have rows and want to populate derived fields, use a data migration or management command to recompute values safely.

---

## Documentation link

This repository includes a simple docs UI at `docs/index.html` — update that file if you'd like to customize styling or content further.

(You can update this link in the README later.)
