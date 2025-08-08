import os
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from pyhanko import stamp
from pyhanko.pdf_utils import images
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from flask import send_file
from io import BytesIO
import hvac

from ..utils import (
    removeUnWantedFiles,
    findCertAvailability,
    genIdByEmail,
    checkFileAvailability,
    download_pdf_from_url
)
from ..config import firebase_config  # ensures firebase_admin.initialize_app() is run
from dotenv import load_dotenv

load_dotenv()


class PDFDigitallySigner:
    def __init__(
            self, input_pdf_url, signer_email, stamp_image_path,
            signature_field_name='Signature',
            signature_box=(375, 700, 575, 762)
    ):
        self.signer_email = signer_email
        self.unique_id = genIdByEmail(signer_email)

        self.input_pdf_url = input_pdf_url
        self.input_fixed_pdf = f"outputs/final_fixed_{self.unique_id}.pdf"

        self.stamp_image_path = stamp_image_path
        self.signature_field_name = signature_field_name
        self.signature_box = signature_box

        # Vault client setup
        self.vault_client = hvac.Client(
            url=os.getenv("VAULT_ADDR"),
            token=os.getenv("VAULT_TOKEN")
        )
        self.vault_base_path = f"secret/certs/{self.unique_id}"

    def convert_to_standard_pdf(self):
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
            with open(self.input_fixed_pdf, "wb") as f:
                writer.write(f)
            return {"type": "success", "message": "Successfully converted PDF to signing mode."}
        except Exception as e:
            return {"type": "error", "message": f"Cannot convert PDF: {str(e)}"}

    # def get_certs_from_vault(self):
    #     try:
    #         key_data = self.vault_client.secrets.kv.v2.read_secret_version(path=f"{self.vault_base_path}/signer_key")
    #         cert_data = self.vault_client.secrets.kv.v2.read_secret_version(path=f"{self.vault_base_path}/signer_cert")
    #         # chain_data = self.vault_client.secrets.kv.v2.read_secret_version(path=f"{self.vault_base_path}/ca_chain")
    #
    #         private_key_pem = key_data['data']['data']['content'].encode('utf-8')
    #         cert_pem = cert_data['data']['data']['content'].encode('utf-8')
    #         # chain_pem = chain_data['data']['data']['content'].encode('utf-8')
    #
    #         # return private_key_pem, cert_pem, [chain_pem]
    #         return private_key_pem, cert_pem
    #     except Exception as e:
    #         raise RuntimeError(f"Error fetching certificate data from Vault: {str(e)}")

    import hvac.exceptions

    # Assuming this function is part of the same class
    def get_certs_from_vault(self):

        from ..controllers.keyManage_controller import generateKeys
        """
        Fetches certificate data from Vault. If the secrets don't exist,
        it calls a function to generate and store them.
        """
        try:
            # Attempt to read the private key. If this fails, the secret doesn't exist.
            key_data = self.vault_client.secrets.kv.v2.read_secret_version(path=f"{self.vault_base_path}/signer_key")

            # If the key read is successful, we can assume the cert is also there
            # and proceed to read it.
            cert_data = self.vault_client.secrets.kv.v2.read_secret_version(path=f"{self.vault_base_path}/signer_cert")

            private_key_pem = key_data['data']['data']['content'].encode('utf-8')
            cert_pem = cert_data['data']['data']['content'].encode('utf-8')

            return private_key_pem, cert_pem

        except hvac.exceptions.InvalidRequest as e:
            # This exception is raised when the path does not exist.
            # This is our trigger to generate the certificates.
            print("Certificates not found. Calling generation function.")
            return generateKeys()
        except Exception as e:
            # Catch any other unexpected errors
            raise RuntimeError(f"Error fetching certificate data from Vault: {str(e)}")

    def sign_pdf(self):
        if not checkFileAvailability(self.input_fixed_pdf):
            print("no pdf to sign")
            return {"type": "error", "message": "PDF Not Found."}

        try:
            # private_key_pem, cert_pem, ca_chain_pems = self.get_certs_from_vault()
            private_key_pem, cert_pem = self.get_certs_from_vault()
            pdfSigner = signers.SimpleSigner.load(
                private_key_pem,
                cert_pem,
                # ca_chain_pems=ca_chain_pems
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
                    location="Uva Wellassa University",
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

                signed_pdf_io = BytesIO()
                pdf_signer.sign_pdf(w, output=signed_pdf_io)
                signed_pdf_io.seek(0)

            return send_file(
                signed_pdf_io,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='signed_document.pdf'
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"type": "error", "message": f"PDF signing failed: {str(e)}"}

    def run(self):
        res1 = self.convert_to_standard_pdf()
        if res1["type"] == "error":
            return res1, None
        res2 = self.sign_pdf()
        return res1, res2
