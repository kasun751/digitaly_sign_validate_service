from flask import jsonify, request
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
        res1, res2 = signer.run()
        status_code = 201 if res2 and res2.get("type") == "success" else 500
        return jsonify({
            "conversion_result": res1,
            "signature_result": res2
        }), status_code

    except Exception as e:
        print("error:", str(e))
        return jsonify({
            "error": str(e)
        }), 500
