from flask import Flask, request, jsonify
import os


def documentUpload():
    if 'pdf' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['pdf']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)

    return jsonify({"message": f"PDF received and saved to {file_path}"}), 200
