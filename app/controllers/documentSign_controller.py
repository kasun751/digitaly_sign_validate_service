from flask import request, jsonify, send_file
from ..services.pdfDigitallySign_service import PDFSigner


def documentSign():
    try:
        file = request.files['pdfFile']
        email = request.form.get("email")
        if not file or not email:
            return jsonify({"error": "Missing file or email"}), 400

        signer = PDFSigner(file, email)
        signed_path = signer.sign_pdf()
        return send_file(signed_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
