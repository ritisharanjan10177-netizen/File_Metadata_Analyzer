from flask import Flask, render_template, request, redirect, session
import sys
import os
import sqlite3
from datetime import datetime

project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(project_folder)

from database.database import (
    create_database,
    add_file,
    get_all_files
)

from app.scanner import scan_folder


app = Flask(
    __name__,
    template_folder="../templates"
)

app.secret_key = "file_metadata_secret_key"

create_database()


# --------------------------------------------------
# CLEAR DATABASE
# --------------------------------------------------

def clear_database():

    database_path = os.path.join(
        project_folder,
        "database",
        "files.db"
    )

    connection = sqlite3.connect(
        database_path
    )

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM files"
    )

    connection.commit()

    connection.close()


# --------------------------------------------------
# GET FILE CATEGORY
# --------------------------------------------------

def get_category(file_type):

    file_type = file_type.lower()

    if file_type in [
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".xls",
        ".xlsx"
    ]:
        return "document"

    elif file_type in [
        ".ppt",
        ".pptx"
    ]:
        return "presentation"

    elif file_type in [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp"
    ]:
        return "image"

    else:
        return "other"


# --------------------------------------------------
# PREPARE FILE DATA
# --------------------------------------------------

def prepare_file_data(file):

    current_time = datetime.now()

    try:

        modified_date = datetime.strptime(
            file[5],
            "%Y-%m-%d %H:%M:%S"
        )

        age = (
            current_time - modified_date
        ).days

    except Exception:

        age = 0


    file_size = file[3]


    if file_size < 1024:

        readable_size = f"{file_size} B"

    elif file_size < 1024 * 1024:

        readable_size = f"{round(file_size / 1024, 2)} KB"

    else:

        readable_size = f"{round(file_size / (1024 * 1024), 2)} MB"


    if file_size < 1 * 1024 * 1024:

        size_category = "Small"

    elif file_size <= 10 * 1024 * 1024:

        size_category = "Medium"

    else:

        size_category = "Large"


    return {
        "id": file[0],
        "name": file[1],
        "type": file[2],
        "size": readable_size,
        "size_category": size_category,
        "created": file[4],
        "modified": file[5],
        "accessed": file[6],
        "path": file[7],
        "hash": file[8],
        "age": age,
        "category": get_category(file[2])
    }


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():

    # Reset dashboard after actual browser refresh
    if request.args.get("reset") == "1":

        clear_database()

        session["folder_path"] = ""


    # Get all files
    all_files = get_all_files()

    files = all_files.copy()


    # --------------------------------------------------
    # FILE TYPE / CATEGORY FILTER
    # --------------------------------------------------

    selected_type = request.args.get(
        "file_type",
        "all"
    ).lower()


    if selected_type != "all":

        filtered_files = []

        for file in files:

            file_extension = file[2].lower()

            file_category = get_category(
                file_extension
            )


            # Specific extension
            if selected_type.startswith("."):

                if file_extension == selected_type:

                    filtered_files.append(file)


            # Category
            else:

                if file_category == selected_type:

                    filtered_files.append(file)


        files = filtered_files


    # --------------------------------------------------
    # SORTING
    # --------------------------------------------------

    selected_sort = request.args.get(
        "sort",
        "name"
    ).lower()


    selected_direction = request.args.get(
        "direction",
        "asc"
    ).lower()


    reverse_order = (
        selected_direction == "desc"
    )


    if selected_sort == "name":

        files.sort(
            key=lambda file: file[1].lower(),
            reverse=reverse_order
        )


    elif selected_sort == "size":

        files.sort(
            key=lambda file: file[3],
            reverse=reverse_order
        )


    elif selected_sort == "modified":

        files.sort(
            key=lambda file: file[5],
            reverse=reverse_order
        )


    elif selected_sort == "age":

        files.sort(
            key=lambda file: (
                datetime.strptime(
                    file[5],
                    "%Y-%m-%d %H:%M:%S"
                )
                if file[5]
                else datetime.min
            ),
            reverse=reverse_order
        )


    # --------------------------------------------------
    # DOCUMENT / IMAGE COUNTS
    # --------------------------------------------------

    documents = 0
    images = 0


    for file in files:

        category = get_category(
            file[2]
        )


        if category in [
            "document",
            "presentation"
        ]:

            documents += 1


        if category == "image":

            images += 1


    # --------------------------------------------------
    # FILE TYPE ANALYTICS
    # --------------------------------------------------

    document_count = 0
    presentation_count = 0
    image_count = 0
    other_count = 0


    for file in files:

        category = get_category(
            file[2]
        )


        if category == "document":

            document_count += 1


        elif category == "presentation":

            presentation_count += 1


        elif category == "image":

            image_count += 1


        else:

            other_count += 1


    # --------------------------------------------------
    # TOTAL STORAGE
    # --------------------------------------------------

    total_storage_bytes = 0


    for file in files:

        total_storage_bytes += file[3]


    total_storage_mb = (
        total_storage_bytes /
        (1024 * 1024)
    )


    total_storage_mb = round(
        total_storage_mb,
        2
    )


    # --------------------------------------------------
    # DUPLICATE DETECTION
    # --------------------------------------------------

    hash_groups = {}


    for file in files:

        file_hash = file[8]


        if file_hash:

            if file_hash not in hash_groups:

                hash_groups[file_hash] = []


            hash_groups[file_hash].append(file)


    duplicate_count = 0
    duplicate_groups = []


    for file_hash, group in hash_groups.items():

        if len(group) > 1:

            duplicate_count += (
                len(group) - 1
            )


            duplicate_files = []


            for file in group:

                duplicate_files.append(
                    prepare_file_data(file)
                )


            duplicate_groups.append({

                "hash": file_hash,

                "files": duplicate_files

            })


    # --------------------------------------------------
    # PREPARE FILE DATA
    # --------------------------------------------------

    file_data = []


    for file in files:

        file_data.append(
            prepare_file_data(file)
        )


    # --------------------------------------------------
    # SEND DATA TO HTML
    # --------------------------------------------------

    return render_template(

        "index.html",

        files=file_data,

        total_files=len(file_data),

        documents=documents,

        images=images,

        duplicates=duplicate_count,

        total_storage=total_storage_mb,

        duplicate_groups=duplicate_groups,

        selected_type=selected_type,

        selected_sort=selected_sort,

        selected_direction=selected_direction,

        document_count=document_count,

        presentation_count=presentation_count,

        image_count=image_count,

        other_count=other_count,

        folder_path=session.get(
            "folder_path",
            ""
        )
    )


# --------------------------------------------------
# DETAILS PAGE
# --------------------------------------------------

@app.route("/details/<int:file_id>")
def details(file_id):

    files = get_all_files()

    selected_file = None


    for file in files:

        if file[0] == file_id:

            selected_file = file

            break


    if selected_file is None:

        return "File not found."


    file_data = prepare_file_data(
        selected_file
    )


    return render_template(
        "details.html",
        file=file_data
    )


# --------------------------------------------------
# SCAN FOLDER
# --------------------------------------------------

@app.route(
    "/scan",
    methods=["POST"]
)
def scan():

    folder_path = request.form.get(
        "folder_path"
    )


    if not folder_path:

        return "Please enter a folder path."


    if not os.path.exists(folder_path):

        return "Folder does not exist."


    scanned_files = scan_folder(
        folder_path
    )


    session["folder_path"] = folder_path


    for file_info in scanned_files:

        add_file(file_info)


    return redirect("/")


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )