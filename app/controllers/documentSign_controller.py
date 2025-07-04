from flask import jsonify
from flask import request
from ..utils import getTokenData

from ..services import PDFDigitallySigner


def signDocument():
    payload = getTokenData()
    if not payload['status']:
        return jsonify({"error": "Invalid token"}), 401

    signer_email = payload["signer_email"]
    input_pdf_url = request.form["pdf_url"]

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

        # Run signing — this returns a Flask response or error dict
        sign_response = signer.sign_pdf()
        if isinstance(sign_response, dict) and sign_response.get("type") == "error":
            return jsonify({"error": sign_response["message"]}), 500

        # If no error, return the signed PDF response directly
        return sign_response

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
