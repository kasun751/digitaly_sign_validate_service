from flask import jsonify, request, send_file
from io import BytesIO
from ..utils import getTokenData
from ..services.pdfDigitallySign_service import PDFDigitallySigner


def signDocument():
    payload = getTokenData()
    if not payload or not payload.get('status'):
        print("error: Invalid token")
        return jsonify({"error": "Invalid token"}), 401

    signer_email = payload["signer_email"]
    data = request.get_json()
    input_pdf_url = data.get("pdf_url") or data.get("pdfUrl")
    if not input_pdf_url:
        print("error: pdf_url required")
        return jsonify({"error": "pdf_url required"}), 400

    try:
        signer = PDFDigitallySigner(
            input_pdf_url=input_pdf_url,
            signer_email=signer_email,
            stamp_image_path="static/imgs/stamp.png"
        )

        # Run conversion first
        conversion_result = signer.convert_to_standard_pdf()
        if conversion_result["type"] == "error":
            return jsonify({"error": conversion_result["message"]}), 400

        # Run signing — this returns either Flask response with PDF or error dict
        sign_response = signer.sign_pdf()
        if isinstance(sign_response, dict) and sign_response.get("type") == "error":
            return jsonify({"error": sign_response["message"]}), 500

        # sign_response is Flask's send_file response with PDF bytes and correct headers
        return sign_response

    except Exception as e:
        print("error:", str(e))
        return jsonify({"error": str(e)}), 500
