import sqlite3
import os

DATABASE_NAME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "files.db"
)


def create_database():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            file_type TEXT,
            file_size INTEGER,
            created_date TEXT,
            modified_date TEXT,
            accessed_date TEXT,
            file_path TEXT UNIQUE,
            file_hash TEXT
        )
    """)

    connection.commit()
    connection.close()


def add_file(file_info):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Check whether this exact file path already exists.
    # This prevents the same folder from being added again.
    cursor.execute(
        """
        SELECT id
        FROM files
        WHERE file_path = ?
        """,
        (file_info["file_path"],)
    )

    existing_file = cursor.fetchone()

    if existing_file is not None:
        connection.close()
        return False

    # Do NOT reject based on file_hash.
    # Different files can have the same hash, and we need
    # to keep them so the application can detect duplicates.

    cursor.execute(
        """
        INSERT INTO files (
            file_name,
            file_type,
            file_size,
            created_date,
            modified_date,
            accessed_date,
            file_path,
            file_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            file_info["file_name"],
            file_info["file_type"],
            file_info["file_size"],
            file_info["created_date"],
            file_info["modified_date"],
            file_info["accessed_date"],
            file_info["file_path"],
            file_info["file_hash"]
        )
    )

    connection.commit()
    connection.close()

    return True


def get_all_files():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM files")
    files = cursor.fetchall()

    connection.close()

    return files