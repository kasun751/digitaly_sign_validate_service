from PyPDF2 import PdfReader


def extract_name_from_pdf(pdf_path: str) -> dict:
    try:
        reader = PdfReader(pdf_path)
        print("[DEBUG] PDF loaded.")

        if "/AcroForm" in reader.trailer["/Root"]:
            print("[DEBUG] AcroForm found.")
            fields = reader.trailer["/Root"]["/AcroForm"].get("/Fields", [])
            for field in fields:
                sig_obj = field.get_object()
                print("[DEBUG] Checking field:", sig_obj)

                if "/V" in sig_obj:
                    signature_dict = sig_obj["/V"]

                    # Key is "/Name" for signer name/email
                    name = signature_dict.get("/Name")
                    if name:
                        print("[DEBUG] Signer name found:", name)
                        return {"error": False, "message": name}

            print("[DEBUG] No signature field with name found.")
            return {"error": True, "message": "No signature name found in PDF."}
        else:
            print("[DEBUG] No AcroForm found.")
            return {"error": True, "message": "No AcroForm found in PDF."}

    except Exception as e:
        print(f"[ERROR] Error extracting name from PDF: {e}")
        return {"error": True, "message": f"Error extracting name: {e}"}
