# First-Devin-Session

A simple journal web app. Write entries as text, upload a photo of a handwritten page, or both.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000.

Entries are stored in `instance/journal.db` (SQLite) and photos in `uploads/`.
