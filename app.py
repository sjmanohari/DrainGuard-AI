from flask import Flask, request, jsonify
from datetime import datetime, timezone
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drainguard.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_type TEXT NOT NULL,
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                municipality TEXT NOT NULL,
                ward TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                severity INTEGER NOT NULL,
                rainfall REAL DEFAULT 0,
                risk_score INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'Low',
                status TEXT DEFAULT 'Pending',
                created_at TEXT NOT NULL
            )
        """)


@app.route("/")
def home():
    return jsonify({
        "project": "DrainGuard AI",
        "message": "Drainage monitoring backend is running",
        "status": "ok"
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "DrainGuard AI"})


@app.route("/api/reports", methods=["POST"])
def create_report():
    data = request.get_json(silent=True) or {}

    required = [
        "issue_type", "state", "district",
        "municipality", "ward", "severity"
    ]
    missing = [
        field for field in required
        if field not in data or str(data[field]).strip() == ""
    ]

    if missing:
        return jsonify({
            "error": "Missing required fields",
            "missing": missing
        }), 400

    try:
        severity = int(data["severity"])
        if not 1 <= severity <= 5:
            raise ValueError
        latitude = float(data["latitude"]) if data.get("latitude") is not None else None
        longitude = float(data["longitude"]) if data.get("longitude") is not None else None
        rainfall = float(data.get("rainfall", 0))

        if not 0 <= rainfall <= 500:
            raise ValueError
        if latitude is not None and not -90 <= latitude <= 90:
            raise ValueError
        if longitude is not None and not -180 <= longitude <= 180:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({
            "error": "Check severity (1-5), rainfall (0-500), and coordinates"
        }), 400

    # Transparent rule-based baseline; not a trained ML model.
    risk_score = round(min(100, severity * 15 + min(rainfall, 50) * 1.1))
    risk_level = (
        "High" if risk_score >= 70
        else "Medium" if risk_score >= 40
        else "Low"
    )

    created_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO reports (
                issue_type, state, district, municipality, ward,
                latitude, longitude, severity, rainfall,
                risk_score, risk_level, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
        """, (
            str(data["issue_type"]).strip(),
            str(data["state"]).strip(),
            str(data["district"]).strip(),
            str(data["municipality"]).strip(),
            str(data["ward"]).strip(),
            latitude, longitude, severity, rainfall,
            risk_score, risk_level, created_at
        ))
        report_id = cursor.lastrowid

    return jsonify({
        "id": report_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "status": "Pending",
        "created_at": created_at
    }), 201


@app.route("/api/reports", methods=["GET"])
def list_reports():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY id DESC"
        ).fetchall()

    return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
