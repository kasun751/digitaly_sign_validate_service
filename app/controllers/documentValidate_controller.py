from flask import jsonify, request
from ..services import PDFVerifier


# def documentVarify():
#     try:
#         # Try to fetch filePath from JSON or form
#         pdf_url = None
#         if request.is_json:
#             pdf_url = request.get_json().get("ValidatePdf_url")
#         else:
#             pdf_url = request.form.get("ValidatePdf_url")
#         if not pdf_url:
#             return jsonify({"error": "Missing 'filePath' parameter"}), 400
#
#         verifier = PDFVerifier(signed_pdf_url=pdf_url)
#         res = verifier.print_signature_status()
#         return jsonify(res)
#
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

def documentVarify():
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"error": "Missing file"}), 400

        file = request.files['pdf_file']

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        verifier = PDFVerifier(signed_pdf_file=file)
        res = verifier.print_signature_status()
        return jsonify(res)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
