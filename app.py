import os
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

# Use the DATABASE_PATH environment variable if provided.
# Otherwise, create notes.db in the project folder.
DATABASE_PATH = os.environ.get("DATABASE_PATH", "notes.db")


def get_db_connection():
    """Open a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the notes table if it does not already exist."""
    connection = get_db_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


@app.route("/notes", methods=["GET"])
def get_notes():
    """Return all saved notes."""
    connection = get_db_connection()

    notes = connection.execute(
        """
        SELECT id, content, created_at
        FROM notes
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return jsonify([dict(note) for note in notes]), 200


@app.route("/notes", methods=["POST"])
def create_note():
    """Create and save a new note."""
    data = request.get_json(silent=True)

    if not data or "content" not in data:
        return jsonify(
            {"error": "Request body must contain a 'content' field"}
        ), 400

    content = data["content"]

    if not isinstance(content, str):
        return jsonify(
            {"error": "'content' must be a string"}
        ), 400

    content = content.strip()

    if not content:
        return jsonify(
            {"error": "Note content cannot be empty"}
        ), 400

    connection = get_db_connection()

    cursor = connection.execute(
        "INSERT INTO notes (content) VALUES (?)",
        (content,)
    )

    connection.commit()

    note = connection.execute(
        """
        SELECT id, content, created_at
        FROM notes
        WHERE id = ?
        """,
        (cursor.lastrowid,)
    ).fetchone()

    connection.close()

    return jsonify(dict(note)), 201


@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    """Delete a note by its ID."""
    connection = get_db_connection()

    note = connection.execute(
        "SELECT id FROM notes WHERE id = ?",
        (note_id,)
    ).fetchone()

    if note is None:
        connection.close()
        return jsonify(
            {"error": f"Note with ID {note_id} was not found"}
        ), 404

    connection.execute(
        "DELETE FROM notes WHERE id = ?",
        (note_id,)
    )

    connection.commit()
    connection.close()

    return jsonify(
        {"message": f"Note {note_id} deleted successfully"}
    ), 200


@app.route("/", methods=["GET"])
def home():
    """Basic health-check route."""
    return jsonify(
        {
            "message": "CloudNotes API is running",
            "endpoints": {
                "GET /notes": "List all notes",
                "POST /notes": "Create a note",
                "DELETE /notes/<id>": "Delete a note"
            }
        }
    ), 200


if __name__ == "__main__":
    initialize_database()

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )