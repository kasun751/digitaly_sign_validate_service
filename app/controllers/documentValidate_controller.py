from flask import jsonify, request
from ..services import PDFVerifier


def documentVarify():
    try:
        if 'pdfFile' not in request.files:
            return jsonify({"error": "Missing file"}), 400

        file = request.files['pdfFile']

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        verifier = PDFVerifier(signed_pdf_file=file)
        res = verifier.print_signature_status()
        return jsonify(res)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
