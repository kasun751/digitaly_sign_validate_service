from flask import jsonify
from flask import request
from ..utils import getTokenData

from ..services import PDFDigitallySigner


def signDocument():
    payload = getTokenData()
    if not payload['status']:
        return
    signer_email = payload["signer_email"]
    input_pdf_url = request.form["pdf_url"]
    try:
        signer = PDFDigitallySigner(
            input_pdf_url=input_pdf_url,
            signer_email = signer_email,
            stamp_image_path="static/imgs/stamp.png"
        )
        res1, res2 = signer.run()
        return jsonify({
            "conversion_result": res1,
            "signature_result": res2
        }), 201

    except Exception as e:
        return jsonify({
            "error": str(e),
            "conversion_result": res1 if 'res1' in locals() else {},
            "signature_result": res2 if 'res2' in locals() else {}
        }), 500
