from flask import jsonify, request
from ..services.pdfValidate_service import PDFVerifier
from ..dto.PDFSignatureInfo import PDFSignatureInfo  # import your DTO


def parse_validation_result(res_text: str) -> PDFSignatureInfo:
    """Parse PyHanko's validation output into PDFSignatureInfo DTO."""
    info = PDFSignatureInfo()

    # Signer details
    if "Certificate subject:" in res_text:
        subj_line = res_text.split("Certificate subject:")[1].split("\n")[0].strip()
        if "Email Address:" in subj_line:
            info.signer_email = subj_line.split("Email Address:")[1].split(",")[0].strip()
        if "Common Name:" in subj_line:
            info.signer_common_name = subj_line.split("Common Name:")[1].split(",")[0].strip()
        if "Organization:" in subj_line:
            info.signer_organization = subj_line.split("Organization:")[1].split(",")[0].strip()

    # Trust details
    if "Trust anchor:" in res_text:
        info.trust_anchor = res_text.split("Trust anchor:")[1].split("\n")[0].strip()
    if "the signer's certificate is trusted" in res_text.lower():
        info.is_trusted = True

    # Integrity details
    if "cryptographically sound" in res_text.lower():
        info.is_signature_valid = True
    if "signature mechanism used was" in res_text.lower():
        info.signature_mechanism = res_text.split("signature mechanism used was")[1] \
            .split(".")[0].replace("'", "").strip()

    # Signing time
    if "Signing time as reported by signer:" in res_text:
        info.signing_time = res_text.split("Signing time as reported by signer:")[1] \
            .split("\n")[0].strip()

    # File coverage
    if "covers the entire file" in res_text.lower():
        info.covers_entire_file = True

    # Bottom line — handle both trusted and untrusted cases
    if "Bottom line" in res_text:
        # Trusted case
        bottom_line_text = res_text.split("Bottom line")[1].strip()
        if "\n" in bottom_line_text:
            bottom_line_text = bottom_line_text.split("\n", 1)[1].strip()
        info.bottom_line = bottom_line_text
    else:
        # Untrusted case — search for "The signature is judged"
        for line in res_text.splitlines():
            if "The signature is judged" in line:
                info.bottom_line = line.strip()
                break

    return info

def documentVarify():
    try:
        if 'pdfFile' not in request.files:
            print("[ERROR] Missing file in request.")
            return jsonify({"error": "Missing file"}), 400

        file = request.files['pdfFile']
        if file.filename.strip() == '':
            print("[ERROR] No file selected.")
            return jsonify({"error": "No file selected"}), 400

        verifier = PDFVerifier(signed_pdf_file=file)
        res_text = verifier.print_signature_status()
        print("[DEBUG] ", res_text)
        # Parse into DTO
        dto = parse_validation_result(res_text)
        print("[DEBUG] ", dto)

        return jsonify({"status": "success", "details": dto.to_dict()}), 200

    except ValueError as e:
        print("[VALIDATION ERROR]", str(e))
        return jsonify({"status": "failed", "error": str(e)}), 400

    except RuntimeError as e:
        print("[RUNTIME ERROR]", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

    except Exception as e:
        print("[UNEXPECTED ERROR]", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
