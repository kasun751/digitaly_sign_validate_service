from flask import jsonify, request
from ..services.pdfValidate_service import PDFVerifier


def documentVarify():
    try:
        # 1. Check if file exists in request
        if 'pdfFile' not in request.files:
            print("[ERROR] Missing file in request.")
            return jsonify({"error": "Missing file"}), 400

        file = request.files['pdfFile']
        if file.filename.strip() == '':
            print("[ERROR] No file selected.")
            return jsonify({"error": "No file selected"}), 400

        # 2. Verify PDF
        verifier = PDFVerifier(signed_pdf_file=file)
        res = verifier.print_signature_status()

        return jsonify({"status": "success", "details": res}), 200

    except ValueError as e:
        # Catch unsigned or invalid PDFs
        print("[VALIDATION ERROR]", str(e))
        return jsonify({"status": "failed", "error": str(e)}), 400

    except RuntimeError as e:
        # Catch controlled runtime errors
        print("[RUNTIME ERROR]", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

    except Exception as e:
        # Catch unexpected errors
        print("[UNEXPECTED ERROR]", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
