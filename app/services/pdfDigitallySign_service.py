import os
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from pyhanko import stamp
from pyhanko.pdf_utils import images
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from flask import send_file
from io import BytesIO

from ..utils import (
    removeUnWantedFiles,
    findCertAvailability,
    genIdByEmail,
    checkFileAvailability,
    download_pdf_from_url
)
from ..config import firebase_config  # ensures firebase_admin.initialize_app() is run


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
        self.input_pdf_location = f"outputs/document-signed_{self.unique_id}.pdf"
        self.private_key_path = f"pemFiles/private_key_{self.unique_id}.pem"
        self.cert_path = f"pemFiles/cert_{self.unique_id}.pem"
        self.ca_chain_paths = [f"pemFiles/ca_chain_{self.unique_id}.pem"]

        self.stamp_image_path = stamp_image_path
        self.signature_field_name = signature_field_name
        self.signature_box = signature_box

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

    def sign_pdf(self):
        availability, _ = findCertAvailability(self.signer_email)
        if not availability:
            from ..controllers import generateKeys
            generateKeys()

        if not checkFileAvailability(self.input_fixed_pdf):
            return {"type": "error", "message": "PDF Not Found."}

        try:
            pdfSigner = signers.SimpleSigner.load(
                self.private_key_path,
                self.cert_path,
                ca_chain_files=self.ca_chain_paths
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

                # Instead of writing to disk, write to BytesIO
                signed_pdf_io = BytesIO()
                pdf_signer.sign_pdf(w, output=signed_pdf_io)
                signed_pdf_io.seek(0)

                # removeUnWantedFiles(self.input_fixed_pdf)
                # removeUnWantedFiles(self.input_pdf_url)
                # removeUnWantedFiles(self.input_pdf_location)

            # Return signed PDF as Flask response
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
