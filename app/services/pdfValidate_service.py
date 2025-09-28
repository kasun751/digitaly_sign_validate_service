import os
from pyhanko.keys import load_cert_from_pemder
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature

from ..utils import (
    genIdByEmail,
    extract_name_from_pdf,
    removeUnWantedFiles,
    load_certs_from_vault_to_temp
)


def save_uploaded_file(file):
    """Save uploaded file to a local temp path."""
    local_path = f"outputs/temp_uploaded_{genIdByEmail(file.filename)}.pdf"
    file.save(local_path)
    return local_path


class PDFVerifier:
    def __init__(self, signed_pdf_file):
        """Initialize PDFVerifier with uploaded file."""
        self.signed_pdf_path = save_uploaded_file(signed_pdf_file)

        try:
            # Extract signer email from PDF
            response = extract_name_from_pdf(self.signed_pdf_path)

            if not isinstance(response, dict):
                raise ValueError("Invalid response format from extract_name_from_pdf.")

            if response.get("error"):
                raise ValueError(response.get("message") or "Signer information not found.")

            self.signer_email = response.get("message")
            if not self.signer_email:
                raise ValueError("No signer email found in PDF.")

        except Exception as e:
            self.safe_cleanup(self.signed_pdf_path)
            raise RuntimeError(f"Failed to extract signer email: {e}")

        self.unique_id = genIdByEmail(self.signer_email)
        self.vault_base_path = "certs"

    def load_root_cert(self):
        """Load root CA cert from Vault."""
        try:
            temp_paths = load_certs_from_vault_to_temp(self.signer_email)
            # ca_chain_path = temp_paths.get("ca_chain")
            cert_path = temp_paths.get("root_cert")

            if not cert_path:
                raise FileNotFoundError("CA chain certificate not found in Vault.")

            root_cert = load_cert_from_pemder(cert_path)

            # Clean up temporary CA chain file
            self.safe_cleanup(cert_path)
            return root_cert

        except Exception as e:
            raise RuntimeError(f"Failed to load root cert from Vault: {e}")

    def validate_signature(self):
        """Validate the PDF's digital signature."""
        root_cert = self.load_root_cert()
        vc = ValidationContext(trust_roots=[root_cert])

        with open(self.signed_pdf_path, "rb") as doc:
            reader = PdfFileReader(doc)
            if not reader.embedded_signatures:
                raise ValueError("No embedded digital signature found in the PDF.")

            sig = reader.embedded_signatures[0]
            return validate_pdf_signature(sig, vc, skip_diff=True)

    def print_signature_status(self):
        """Run validation and return human-readable result."""
        try:
            status = self.validate_signature()
            return status.pretty_print_details()
        finally:
            self.safe_cleanup(self.signed_pdf_path)

    @staticmethod
    def safe_cleanup(path):
        """Safely remove a file without raising exceptions."""
        try:
            removeUnWantedFiles(path)
        except Exception as cleanup_err:
            print(f"[WARNING] Failed to remove temp file {path}: {cleanup_err}")
