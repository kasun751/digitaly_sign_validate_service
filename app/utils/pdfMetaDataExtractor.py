from PyPDF2 import PdfReader


# import os

def extract_name_from_pdf(pdf_path: str) -> dict:
    try:
        reader = PdfReader(pdf_path)
        print("PDF loaded.")

        if "/AcroForm" in reader.trailer["/Root"]:
            print("AcroForm found.")
            fields = reader.trailer["/Root"]["/AcroForm"].get("/Fields", [])
            for field in fields:
                sig_obj = field.get_object()
                print("Checking field:", sig_obj)

                if "/V" in sig_obj:
                    signature_dict = sig_obj["/V"]

                    # Correct key is "/Name", not "/name"
                    name = signature_dict.get("/Name")
                    if name:
                        print("Name found:", name)
                        return {"error": False, "message": name}
                    else:
                        return {"error": True, "message": "Not Found Email"}

        else:
            print("No AcroForm found.")
            return {"error": True, "message": "Signature Not Found."}

    except Exception as e:
        print(f"Error extracting name from PDF: {e}")
        return {"error": True, "message": f"Error extracting name from PDF: {e}"}
