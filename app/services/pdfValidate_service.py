from pyhanko.keys import load_cert_from_pemder
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from ..utils import extract_name_from_pdf, save_file_in_local, removeUnWantedFiles
from app.vault_client import VaultClient


class PDFVerifier:
    def __init__(self, signed_pdf_file):
        self.signed_pdf_path = save_file_in_local(signed_pdf_file)
        response = extract_name_from_pdf(self.signed_pdf_path)
        if response["error"]:
            raise Exception(response["message"])
        self.signer_email = response["message"]
        self.vault = VaultClient()

    def load_root_cert(self):
        cert_pem = self.vault.get_certificate(self.signer_email)
        return load_cert_from_pemder(cert_pem)

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
