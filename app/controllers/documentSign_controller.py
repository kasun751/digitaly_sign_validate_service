import requests
from flask import request, jsonify, send_file
import io
from ..services import CertificateAuthorityService


def documentSign():
    try:
        data = request.get_json()
        if not data or 'pdfUrl' not in data:
            return jsonify({"error": "pdfUrl is required in the request body"}), 400

        pdf_url = data['pdfUrl']
        print("Downloading from URL:", pdf_url)

        # 📥 Download the PDF from the provided URL
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download PDF from provided URL"}), 400

        pdf_bytes = response.content

        # 🔏 Digitally sign the PDF
        print("before")
        ca_service = CertificateAuthorityService()
        print("mid")
        signed_pdf_bytes = ca_service.sign_pdf(pdf_data=pdf_bytes)
        print("after")

        # 📤 Return the signed PDF
        return send_file(
            io.BytesIO(signed_pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='signed_document.pdf'
        )

    except Exception as e:
        print("Error during signing:", str(e))
        return jsonify({"error": str(e)}), 500
