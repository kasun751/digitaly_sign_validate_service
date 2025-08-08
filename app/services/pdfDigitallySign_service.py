import os
import logging
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from pyhanko import stamp
from pyhanko.pdf_utils import images
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from ..utils.fileUtills import (
    download_pdf_from_url,
    findCertAvailability,
    load_certs_from_vault_to_temp,
    removeUnWantedFiles
)
from ..utils.generateIdByEmail import genIdByEmail

logger = logging.getLogger(__name__)


class PDFDigitallySigner:
    def __init__(
        self, input_pdf_url, signer_email, stamp_image_path,
        signature_field_name='Signature',
        signature_box=(375, 700, 575, 762),
        vault_base_path="certs"
    ):
        self.signer_email = signer_email
        self.unique_id = genIdByEmail(signer_email)
        self.input_pdf_url = input_pdf_url
        self.input_fixed_pdf = f"outputs/final_fixed_{self.unique_id}.pdf"
        self.input_pdf_location = f"outputs/document-signed_{self.unique_id}.pdf"
        self.stamp_image_path = stamp_image_path
        self.signature_field_name = signature_field_name
        self.signature_box = signature_box
        self.vault_base_path = vault_base_path

    def convert_to_standard_pdf(self):
        # accept remote URL or local path
        if self.input_pdf_url.startswith("http://") or self.input_pdf_url.startswith("https://"):
            downloaded_path = download_pdf_from_url(self.input_pdf_url)
            if not downloaded_path:
                return {"type": "error", "message": "Failed to download PDF from URL."}
            self.input_pdf_url = downloaded_path

        try:
            reader = PdfReader(self.input_pdf_url)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            os.makedirs(os.path.dirname(self.input_fixed_pdf), exist_ok=True)
            with open(self.input_fixed_pdf, "wb") as f:
                writer.write(f)
            return {"type": "success", "message": "Successfully converted PDF to signing mode."}
        except Exception as e:
            logger.exception("PDF conversion error")
            return {"type": "error", "message": f"Cannot convert PDF: {str(e)}"}

    def sign_pdf(self):
        # 1) Ensure certs exist in Vault; generate if missing
        availability, missing = findCertAvailability(self.signer_email, vault_base_path=self.vault_base_path)
        if availability is None:
            print("Internal error checking cert availability.")
            return {"type": "error", "message": "Internal error checking cert availability."}

        if not availability:
            from ..controllers.keyManage_controller import generateKeys
            logger.info("Certs missing in Vault (%s). Generating keys: %s", self.signer_email, missing)
            # Generate keys programmatically using controller/service
            # generateKeys will store into Vault
            # gen_response, status = generateKeys(signer_email=self.signer_email, signer_cn=self.signer_email, vault_base_path=self.vault_base_path)
            gen_response, status = generateKeys()
            # if generateKeys returned a Flask response tuple, handle it
            if isinstance(gen_response, tuple):
                # expect (jsonify(...), status_code)
                if status != 201:
                    return {"type": "error", "message": "Failed to generate keys before signing."}

        # 2) Load certs from Vault into temp files
        try:
            temp_paths = load_certs_from_vault_to_temp(self.signer_email, vault_base_path=self.vault_base_path)
            private_key_path = temp_paths["private_key"]
            cert_path = temp_paths["cert"]
            ca_chain_paths = [temp_paths["ca_chain"]]
        except Exception as e:
            logger.exception("Failed to load certs from Vault into temp files")
            return {"type": "error", "message": f"Failed to load certs: {str(e)}"}

        # 3) Check fixed PDF availability
        if not os.path.isfile(self.input_fixed_pdf):
            # cleanup temp certs
            removeUnWantedFiles(private_key_path)
            removeUnWantedFiles(cert_path)
            removeUnWantedFiles(ca_chain_paths[0])
            return {"type": "error", "message": "PDF Not Found."}

        # 4) Do the signing with pyHanko
        try:
            pdfSigner = signers.SimpleSigner.load(
                private_key_path,
                cert_path,
                ca_chain_files=ca_chain_paths
            )

            with open(self.input_fixed_pdf, 'rb') as inf:
                w = IncrementalPdfFileWriter(inf)

                fields.append_signature_field(
                    w,
                    sig_field_spec=fields.SigFieldSpec(
                        self.signature_field_name,
                        box=self.signature_box
                    )
                )

                meta = signers.PdfSignatureMetadata(
                    field_name=self.signature_field_name,
                    location=os.getenv("SIGN_LOCATION", "Uva Wellassa University"),
                    contact_info=self.signer_email,
                    name=self.signer_email,
                    reason="Document Approval"
                )

                stamp_text = f"Signed by: {self.signer_email}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                pdf_signer = signers.PdfSigner(
                    meta,
                    signer=pdfSigner,
                    stamp_style=stamp.TextStampStyle(
                        stamp_text=stamp_text,
                        background=images.PdfImage(self.stamp_image_path)
                    )
                )

                os.makedirs(os.path.dirname(self.input_pdf_location), exist_ok=True)

                with open(self.input_pdf_location, 'wb') as outf:
                    pdf_signer.sign_pdf(w, output=outf)

            # 5) Upload to Firebase
            # public_url = upload_pdf_to_firebase(self.input_pdf_location)

            # 6) Cleanup local files (temp pdfs and temp pem files)
            removeUnWantedFiles(self.input_fixed_pdf)
            # if input_pdf_url was downloaded to temp_download, remove it too
            if self.input_pdf_url.startswith("temp_download/") or self.input_pdf_url.startswith("temp_"):
                removeUnWantedFiles(self.input_pdf_url)
            removeUnWantedFiles(self.input_pdf_location)
            removeUnWantedFiles(private_key_path)
            removeUnWantedFiles(cert_path)
            for ca in ca_chain_paths:
                removeUnWantedFiles(ca)

            return {
                "type": "success",
                "message": "Successfully signed and uploaded PDF.",
                "firebase_url": public_url
            }

        except Exception as e:
            logger.exception("Signing failed")
            # Ensure cleanup of temp certs even on failure
            removeUnWantedFiles(private_key_path)
            removeUnWantedFiles(cert_path)
            for ca in ca_chain_paths:
                removeUnWantedFiles(ca)
            return {"type": "error", "message": f"PDF signing failed: {str(e)}"}

    def run(self):
        res1 = self.convert_to_standard_pdf()
        if res1["type"] == "error":
            return res1, None
        res2 = self.sign_pdf()
        return res1, res2
