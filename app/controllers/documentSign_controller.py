from flask import request, jsonify, send_file
import io
from ..services import CertificateAuthorityService
# from ..services.pdfDigitallySign_service import PDFSigner


def documentSign():
    if 'pdfFile' not in request.files:
        return jsonify({"error": "PDF file is required"}), 400

    file = request.files['pdfFile']
    pdf_bytes = file.read()

    try:
        # Sign using service
        signed_pdf_bytes = CertificateAuthorityService.sign_pdf(pdf_bytes)

        # Return signed PDF as response
        return send_file(
            io.BytesIO(signed_pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='signed_document.pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
