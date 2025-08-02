import io
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko_certvalidator import ValidationContext
from app.utils.vault_manager import load_private_key_and_cert  # Custom utility


class CertificateAuthorityService:

    @staticmethod
    def sign_pdf(pdf_data: bytes) -> bytes:
        # Load from Vault (or secure source)
        private_key, cert = load_private_key_and_cert()

        signer = signers.SimpleSigner(
            signing_cert=cert,
            signing_key=private_key,
            cert_registry=signers.SimpleCertificateStore([cert]),
            validation_context=ValidationContext()
        )

        pdf_reader = IncrementalPdfFileWriter(io.BytesIO(pdf_data))

        signed_pdf = signers.sign_pdf(
            pdf_reader,
            signature_meta=signers.PdfSignatureMetadata(field_name="Signature1"),
            signer=signer,
            existing_fields_only=False,
            new_field_spec=SigFieldSpec(sig_field_name="Signature1")
        )

        output = io.BytesIO()
        signed_pdf.write(output)
        output.seek(0)
        return output.read()
