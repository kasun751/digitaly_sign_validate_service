import os
import requests
import uuid
from .idGenerator import genIdByEmail, generate_random_string
from firebase_admin import storage
from flask import request, jsonify


def checkFileAvailability(path):
    if path is None:
        return None
    if os.path.isfile(path):
        return True
    else:
        return False


def checkFileType(path, type):
    if path is None | type is None:
        return None
    if checkFileAvailability(path):
        _, extension = os.path.splitext(path)
        if extension == type:
            return True
        else:
            return False
    return None


def getFileExtension(path):
    if path is None:
        return None
    if checkFileAvailability(path):
        _, extension = os.path.splitext(path)
        return extension
    else:
        return None


def removeUnWantedFiles(path):
    if path is None:
        return None
    if checkFileAvailability(path):
        if os.path.exists(path):
            os.remove(path)
            print("File deleted successfully.")
            return True
        else:
            print("File not found.")
            return False


def findCertAvailability(signer_email, path="pemFiles/"):
    if signer_email is None:
        return None
    signerId = genIdByEmail(signer_email)
    cert_files = {
        "privateKey": "private_key",
        "caChain": "ca_chain",
        "intermediateCert": "intermediate_cert",
        "root_cert": "root_cert"
    }

    for key, value in cert_files.items():
        if os.path.isfile(path + value + "_" + signerId + ".pem"):
            pass
        else:
            return False, "Error : Not Found " + key + "...!!!"
    return True, "message: All Certs are Available"


# def download_pdf_from_url(url):
#     try:
#         unique_filename = f"temp_{uuid.uuid4().hex}.pdf"
#         response = requests.get(url)
#         response.raise_for_status()
#         file_path = 'temp_download/' + unique_filename
#         with open(file_path, 'wb') as f:
#             f.write(response.content)
#         return file_path
#     except Exception as e:
#         print("Error downloading PDF:", e)
#         return None

def download_pdf_from_url(url):
    try:
        # Make sure the temp directory exists
        temp_dir = 'temp_download'
        os.makedirs(temp_dir, exist_ok=True)

        # Use a unique filename
        unique_filename = f"temp_{uuid.uuid4().hex}.pdf"
        file_path = os.path.join(temp_dir, unique_filename)

        # Download with streaming for large files
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        return file_path

    except Exception as e:
        print("Error downloading PDF:", e)
        return None


def upload_pdf_to_firebase(input_pdf_location):
    try:
        bucket = storage.bucket()
        blob_name = f"signed_pdfs/{uuid.uuid4()}_{os.path.basename(input_pdf_location)}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(input_pdf_location, content_type="application/pdf")
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print("Error uploading PDF:", e)
        return None


def save_file_in_local():
    if 'pdf' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return ""
    fileName = generate_random_string()
    file.save(f"temp_download/{fileName}")
    return fileName
