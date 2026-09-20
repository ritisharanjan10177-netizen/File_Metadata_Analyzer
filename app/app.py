from flask import Flask, render_template, request, redirect
import os
import hashlib
from werkzeug.utils import secure_filename

from database.database import (
    create_database,
    add_file,
    get_all_files
)

# --------------------------------------------------
# FLASK APP
# --------------------------------------------------

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_FOLDER = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_PATH = os.path.join(
    PROJECT_FOLDER,
    "database",
    "files.db"
)

UPLOAD_FOLDER = os.path.join(
    PROJECT_FOLDER,
    "scanned_files"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

create_database()


# --------------------------------------------------
# CLEAR DATABASE
# --------------------------------------------------

def clear_database():

    import sqlite3

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM files")

    connection.commit()
    connection.close()


# --------------------------------------------------
# FILE CATEGORY
# --------------------------------------------------

def get_category(file_type):

    extension = file_type.lower()

    document_extensions = {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".xls",
        ".xlsx",
        ".csv"
    }

    presentation_extensions = {
        ".ppt",
        ".pptx"
    }

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".svg"
    }

    if extension in document_extensions:
        return "Documents"

    elif extension in presentation_extensions:
        return "Presentations"

    elif extension in image_extensions:
        return "Images"

    else:
        return "Other"


# --------------------------------------------------
# FORMAT FILE SIZE
# --------------------------------------------------

def format_size(size):

    if size < 1024:
        return f"{size} B"

    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"

    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"

    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


# --------------------------------------------------
# FILE HASH
# --------------------------------------------------

def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            data = file.read(65536)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


# --------------------------------------------------
# CREATE FILE INFORMATION
# --------------------------------------------------

def create_uploaded_file_info(
    file_path,
    file_name
):

    from datetime import datetime

    file_size = os.path.getsize(file_path)

    created_timestamp = os.path.getctime(
        file_path
    )

    modified_timestamp = os.path.getmtime(
        file_path
    )

    accessed_timestamp = os.path.getatime(
        file_path
    )

    created_date = datetime.fromtimestamp(
        created_timestamp
    ).strftime("%Y-%m-%d %H:%M:%S")

    modified_date = datetime.fromtimestamp(
        modified_timestamp
    ).strftime("%Y-%m-%d %H:%M:%S")

    accessed_date = datetime.fromtimestamp(
        accessed_timestamp
    ).strftime("%Y-%m-%d %H:%M:%S")

    file_extension = os.path.splitext(
        file_name
    )[1].lower()

    file_hash = calculate_file_hash(
        file_path
    )

    return {
        "file_name": file_name,
        "file_type": file_extension,
        "file_size": file_size,
        "created_date": created_date,
        "modified_date": modified_date,
        "accessed_date": accessed_date,
        "file_path": file_path,
        "file_hash": file_hash
    }


# --------------------------------------------------
# PREPARE FILE DATA
# --------------------------------------------------

def prepare_file_data(database_file):

    return {
        "id": database_file[0],
        "file_name": database_file[1],
        "file_type": database_file[2],
        "file_size": database_file[3],
        "readable_size": format_size(
            database_file[3]
        ),
        "created_date": database_file[4],
        "modified_date": database_file[5],
        "accessed_date": database_file[6],
        "file_path": database_file[7],
        "file_hash": database_file[8],
        "category": get_category(
            database_file[2]
        )
    }


# --------------------------------------------------
# HOME / DASHBOARD
# --------------------------------------------------

@app.route("/")
def home():

    # Manual reset
    if request.args.get("reset") is not None:

        clear_database()

        return redirect("/")

    database_files = get_all_files()

    files = [
        prepare_file_data(file)
        for file in database_files
    ]

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------

    category_filter = request.args.get(
        "category",
        "All"
    )

    extension_filter = request.args.get(
        "extension",
        "All"
    )

    if category_filter != "All":

        files = [
            file
            for file in files
            if file["category"] == category_filter
        ]

    if extension_filter != "All":

        files = [
            file
            for file in files
            if file["file_type"] == extension_filter
        ]

    # --------------------------------------------------
    # SORTING
    # --------------------------------------------------

    sort_by = request.args.get(
        "sort",
        "name"
    )

    order = request.args.get(
        "order",
        "asc"
    )

    if sort_by == "name":

        files.sort(
            key=lambda x: x["file_name"].lower()
        )

    elif sort_by == "size":

        files.sort(
            key=lambda x: x["file_size"]
        )

    elif sort_by == "modified":

        files.sort(
            key=lambda x: x["modified_date"]
        )

    elif sort_by == "age":

        files.sort(
            key=lambda x: x["created_date"]
        )

    if order == "desc":

        files.reverse()

    # --------------------------------------------------
    # DASHBOARD COUNTS
    # --------------------------------------------------

    total_files = len(files)

    total_size_bytes = sum(
        file["file_size"]
        for file in files
    )

    total_size = format_size(
        total_size_bytes
    )

    documents_count = sum(
        1
        for file in files
        if file["category"] == "Documents"
    )

    presentations_count = sum(
        1
        for file in files
        if file["category"] == "Presentations"
    )

    images_count = sum(
        1
        for file in files
        if file["category"] == "Images"
    )

    other_count = sum(
        1
        for file in files
        if file["category"] == "Other"
    )

    # --------------------------------------------------
    # FILE TYPE DISTRIBUTION
    # --------------------------------------------------

    file_type_distribution = {}

    for file in files:

        extension = file["file_type"]

        if extension == "":
            extension = "No Extension"

        file_type_distribution[extension] = (
            file_type_distribution.get(
                extension,
                0
            ) + 1
        )

    # --------------------------------------------------
    # DUPLICATE FILES
    # --------------------------------------------------

    hash_groups = {}

    for file in files:

        file_hash = file["file_hash"]

        if file_hash not in hash_groups:

            hash_groups[file_hash] = []

        hash_groups[file_hash].append(file)

    duplicate_groups = [
        group
        for group in hash_groups.values()
        if len(group) > 1
    ]

    duplicate_count = sum(
        len(group)
        for group in duplicate_groups
    )

    # --------------------------------------------------
    # EXTENSIONS
    # --------------------------------------------------

    extensions = sorted(
        set(
            file["file_type"]
            for file in files
            if file["file_type"]
        )
    )

    # --------------------------------------------------
    # RENDER PAGE
    # --------------------------------------------------

    return render_template(
        "index.html",

        files=files,

        total_files=total_files,

        total_size=total_size,

        documents_count=documents_count,

        presentations_count=presentations_count,

        images_count=images_count,

        other_count=other_count,

        file_type_distribution=file_type_distribution,

        duplicate_groups=duplicate_groups,

        duplicate_count=duplicate_count,

        category_filter=category_filter,

        extension_filter=extension_filter,

        extensions=extensions,

        sort_by=sort_by,

        order=order
    )


# --------------------------------------------------
# FILE DETAILS
# --------------------------------------------------

@app.route("/details/<int:file_id>")
def details(file_id):

    database_files = get_all_files()

    selected_file = None

    for database_file in database_files:

        if database_file[0] == file_id:

            selected_file = prepare_file_data(
                database_file
            )

            break

    if selected_file is None:

        return "File not found", 404

    return render_template(
        "details.html",
        file=selected_file
    )


# --------------------------------------------------
# SCAN / UPLOAD FOLDER
# --------------------------------------------------

@app.route("/scan", methods=["POST"])
def scan():

    # Start every folder analysis fresh.
    # This prevents 6 -> 12 -> 18.
    clear_database()

    uploaded_files = request.files.getlist(
        "files"
    )

    for uploaded_file in uploaded_files:

        if uploaded_file.filename == "":
            continue

        original_name = os.path.basename(
            uploaded_file.filename
        )

        safe_name = secure_filename(
            original_name
        )

        if not safe_name:
            continue

        save_path = os.path.join(
            UPLOAD_FOLDER,
            safe_name
        )

        # Prevent overwriting
        counter = 1

        base_name, extension = os.path.splitext(
            safe_name
        )

        while os.path.exists(save_path):

            safe_name = (
                f"{base_name}_{counter}{extension}"
            )

            save_path = os.path.join(
                UPLOAD_FOLDER,
                safe_name
            )

            counter += 1

        uploaded_file.save(
            save_path
        )

        file_info = create_uploaded_file_info(
            save_path,
            safe_name
        )

        add_file(file_info)

    return redirect("/")


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )