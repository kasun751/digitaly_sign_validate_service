import io
from datetime import datetime
from pyhanko.sign import signers, fields
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko_certvalidator import ValidationContext
from pyhanko import stamp
from pyhanko.pdf_utils import images
from app.utils.vault_manager import load_private_key_and_cert


class CertificateAuthorityService:
    def __init__(self, **kwargs):
        self.output_dir = kwargs.get("output_dir")
        self.stamp_image_path = kwargs.get("stamp_image_path")
        self.country = kwargs.get("country")
        self.state = kwargs.get("state")
        self.location = kwargs.get("location")
        self.contact_info = kwargs.get("contact_info")
        self.reason = kwargs.get("reason")
        self.locality = kwargs.get("locality")

    def sign_pdf(self, pdf_data: bytes, signer_email: str = None, signature_field_name="Signature1",
                 signature_box=(375, 700, 575, 762)) -> bytes:

        private_key, cert = load_private_key_and_cert()
        print(private_key)
        print(cert)

        signer = signers.SimpleSigner(
            signing_cert=cert,
            signing_key=private_key,
            cert_registry=signers.SimpleCertificateStore([cert]),
            validation_context=ValidationContext()
        )

        pdf_writer = IncrementalPdfFileWriter(io.BytesIO(pdf_data))
        print(pdf_writer)
        print("pdf_writer")

        # Append signature field
        fields.append_signature_field(
            pdf_writer,
            sig_field_spec=SigFieldSpec(signature_field_name, box=signature_box)
        )

        meta = signers.PdfSignatureMetadata(
            field_name=signature_field_name,
            location="Uva Wellassa University",
            contact_info=signer_email or "",
            name=signer_email or "",
            reason="Document Approval"
        )

        # Optional stamp appearance
        if self.stamp_image_path:
            stamp_text = f"Signed by: {signer_email or 'Unknown'}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            stamp_style = stamp.TextStampStyle(
                stamp_text=stamp_text,
                background=images.PdfImage(self.stamp_image_path)
            )
        else:
            stamp_style = None

        pdf_signer = signers.PdfSigner(
            meta,
            signer=signer,
            stamp_style=stamp_style
        )

        output = io.BytesIO()
        pdf_signer.sign_pdf(pdf_writer, output=output)
        output.seek(0)

        signed_pdf_bytes = output.read()
        print(signed_pdf_bytes)

        if self.output_dir:
            import os
            os.makedirs(self.output_dir, exist_ok=True)
            filename = f"signed_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            path = os.path.join(self.output_dir, filename)
            with open(path, "wb") as f:
                f.write(signed_pdf_bytes)
            return None  # Or return path if needed

        return signed_pdf_bytes

    def generate_all(self):
        print("Called generate_all()")
