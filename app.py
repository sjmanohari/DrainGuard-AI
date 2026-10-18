
from flask import Flask, jsonify, request
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

app = Flask(__name__)

# Store the database in the same folder as this file.
DB_PATH = Path(__file__).resolve().parent / "drainguard.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def current_time():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize_database():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                risk_level TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'submitted',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def complaint_dict(row):
    return dict(row)


@app.get("/")
def home():
    return jsonify({
        "message": "DrainGuard AI backend is running",
        "health": "/api/health"
    })


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/complaints")
def create_complaint():
    if not request.is_json:
        return jsonify({"error": "Send JSON data"}), 415

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON object"}), 400

    title = data.get("title")
    description = data.get("description")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Title is required"}), 400

    if not isinstance(description, str) or not description.strip():
        return jsonify({"error": "Description is required"}), 400

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    try:
        if latitude is not None:
            latitude = float(latitude)
            if not -90 <= latitude <= 90:
                raise ValueError

        if longitude is not None:
            longitude = float(longitude)
            if not -180 <= longitude <= 180:
                raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid coordinates"}), 400

    risk = str(data.get("risk_level", "medium")).lower()
    if risk not in {"low", "medium", "high", "critical"}:
        return jsonify({"error": "Invalid risk level"}), 400

    now = current_time()
    complaint_id = "DG-" + uuid.uuid4().hex[:12].upper()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO complaints (
                complaint_id, title, description, latitude,
                longitude, risk_level, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id, title.strip(), description.strip(),
            latitude, longitude, risk, "submitted", now, now
        ))

        row = conn.execute(
            "SELECT * FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        ).fetchone()

    return jsonify({
        "message": "Complaint submitted successfully",
        "complaint": complaint_dict(row)
    }), 201


@app.get("/api/complaints")
def get_complaints():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM complaints ORDER BY created_at DESC"
        ).fetchall()

    return jsonify({
        "count": len(rows),
        "complaints": [complaint_dict(row) for row in rows]
    })


@app.get("/api/complaints/<complaint_id>")
def get_one_complaint(complaint_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        ).fetchone()

    if row is None:
        return jsonify({"error": "Complaint not found"}), 404

    return jsonify({"complaint": complaint_dict(row)})


@app.patch("/api/complaints/<complaint_id>")
def update_complaint(complaint_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({"error": "Provide JSON update data"}), 400

    allowed = {"status", "risk_level"}
    if set(data) - allowed:
        return jsonify({
            "error": "Only status and risk_level can be updated"
        }), 400

    updates = {}

    if "status" in data:
        status = str(data["status"]).lower()
        if status not in {
            "submitted", "under_review", "in_progress",
            "resolved", "rejected"
        }:
            return jsonify({"error": "Invalid status"}), 400
        updates["status"] = status

    if "risk_level" in data:
        risk = str(data["risk_level"]).lower()
        if risk not in {"low", "medium", "high", "critical"}:
            return jsonify({"error": "Invalid risk level"}), 400
        updates["risk_level"] = risk

    if not updates:
        return jsonify({"error": "No valid fields provided"}), 400

    updates["updated_at"] = current_time()
    assignments = ", ".join(
        f"{field} = ?" for field in updates
    )
    values = list(updates.values()) + [complaint_id]

    with get_db() as conn:
        existing = conn.execute(
            "SELECT complaint_id FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        ).fetchone()

        if existing is None:
            return jsonify({"error": "Complaint not found"}), 404

        conn.execute(
            f"UPDATE complaints SET {assignments} WHERE complaint_id = ?",
            values
        )

        row = conn.execute(
            "SELECT * FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        ).fetchone()

    return jsonify({
        "message": "Complaint updated successfully",
        "complaint": complaint_dict(row)
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
