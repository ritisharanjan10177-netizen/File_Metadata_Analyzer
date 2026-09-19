import os
import hashlib
from datetime import datetime


def calculate_hash(file_path):
    """
    Creates a unique fingerprint for the file.
    Files with the same content will have the same hash.
    """

    hash_object = hashlib.md5()

    try:
        with open(file_path, "rb") as file:

            while True:

                data = file.read(4096)

                if not data:
                    break

                hash_object.update(data)

        return hash_object.hexdigest()

    except Exception:
        return ""


def scan_folder(folder_path):

    files = []

    for root, directories, filenames in os.walk(folder_path):

        for filename in filenames:

            file_path = os.path.join(root, filename)

            try:

                # Get file size
                file_size = os.path.getsize(file_path)

                # Get creation date
                created_time = os.path.getctime(file_path)

                # Get modified date
                modified_time = os.path.getmtime(file_path)

                # Get last accessed date
                accessed_time = os.path.getatime(file_path)

                # Calculate file hash
                file_hash = calculate_hash(file_path)

                # Store file information
                file_info = {

                    "file_name": filename,

                    "file_type": os.path.splitext(filename)[1].lower(),

                    "file_size": file_size,

                    "created_date": datetime.fromtimestamp(
                        created_time
                    ).strftime("%Y-%m-%d %H:%M:%S"),

                    "modified_date": datetime.fromtimestamp(
                        modified_time
                    ).strftime("%Y-%m-%d %H:%M:%S"),

                    "accessed_date": datetime.fromtimestamp(
                        accessed_time
                    ).strftime("%Y-%m-%d %H:%M:%S"),

                    "file_path": file_path,

                    "file_hash": file_hash
                }

                files.append(file_info)

            except Exception:
                continue

    return files