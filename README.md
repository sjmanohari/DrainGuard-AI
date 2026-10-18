
# DrainGuard AI Backend

## Requirements
- Python 3
- Flask
- SQLite (included with standard Python installations)

## Start the backend

Open a terminal in this folder and run:

    python3 -m pip install -r requirements.txt
    python3 app.py

If Flask is already installed in the Python environment being used,
the installation step may be skipped.

## Test whether the backend is running

    curl http://127.0.0.1:5000/api/health

Expected response:

    {"status":"ok"}

## API endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/health | Check backend |
| POST | /api/complaints | Submit a complaint |
| GET | /api/complaints | List complaints |
| GET | /api/complaints/ID | View one complaint |
| PATCH | /api/complaints/ID | Update status or risk |

The database file drainguard.db is created automatically.

New complaints receive unique IDs and start with status "submitted".
