from PyPDF2 import PdfReader

# import os


# from PyPDF2 import PdfReader

def extract_name_from_pdf(pdf_path: str) -> str | None:
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
                        return name

        else:
            print("No AcroForm found.")

        return None

    except Exception as e:
        print(f"Error extracting name from PDF: {e}")
        return None

# def checkFileAvailabilitya(path):
#     if path is None:
#         return None
#     if os.path.isfile(path):
#         return True
#     else:
#         return False


# pdf_path = "E:/Learning/testing_project_2/digitaly-sign-validate-service/outputs/document" \
#            "-signed_DcVHdIhpmJRfxkCzE2oU6YslA5YnGSXG.pdf"
#
# email = extract_name_from_pdf(pdf_path)
# print("Signer Email Address:", email)
