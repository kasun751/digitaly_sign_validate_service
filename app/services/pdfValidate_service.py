from pyhanko.keys import load_cert_from_pemder
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from ..utils import genIdByEmail, extract_name_from_pdf
from ..utils import download_pdf_from_url, removeUnWantedFiles, save_file_in_local


def downloadPdf(pdf_url):
    if pdf_url.startswith("http://") or pdf_url.startswith("https://"):
        downloaded_path = download_pdf_from_url(pdf_url)
        if not downloaded_path:
            return {"type": "error", "message": "Failed to download PDF from URL."}
        return downloaded_path


def save_uploaded_file(file):
    local_path = f"outputs/temp_uploaded_{genIdByEmail(file.filename)}.pdf"
    file.save(local_path)
    return local_path


class PDFVerifier:
    def __init__(self, signed_pdf_file):
        # Save uploaded file to local temp path
        self.signed_pdf_path = save_uploaded_file(signed_pdf_file)

        # Extract signer info, same as before
        # self.signer_email = extract_name_from_pdf(self.signed_pdf_path)
        try:
            response = extract_name_from_pdf(self.signed_pdf_path)
            if response["error"]:
                return response["message"]
            else:
                self.signer_email = response["message"]
        except Exception as e:
            return f"Error while Extracting Signer Email: {e}"

        self.unique_id = genIdByEmail(self.signer_email)
        self.root_cert_path = "pemFiles/root_cert_" + self.unique_id + ".pem"

    def load_root_cert(self):
        return load_cert_from_pemder(self.root_cert_path)

    def validate_signature(self):
        root_cert = self.load_root_cert()
        vc = ValidationContext(trust_roots=[root_cert])

        with open(self.signed_pdf_path, "rb") as doc:
            r = PdfFileReader(doc)
            if not r.embedded_signatures:
                raise ValueError("No embedded signature found in the PDF.")
            sig = r.embedded_signatures[0]
            status = validate_pdf_signature(sig, vc, skip_diff=True)
            return status

    def print_signature_status(self):
        status = self.validate_signature()
        removeUnWantedFiles(self.signed_pdf_path)
        return status.pretty_print_details()
