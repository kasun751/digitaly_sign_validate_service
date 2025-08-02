from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from ..vault_client import VaultClient
from ..utils import genIdByEmail, save_file_in_local
import io


class PDFSigner:
    def __init__(self, uploaded_pdf, user_email):
        self.pdf_path = save_file_in_local(uploaded_pdf)
        self.email = user_email
        self.vault = VaultClient()

    def sign_pdf(self):
        cert_pem = self.vault.get_certificate(self.email)
        key_pem = self.vault.get_private_key(self.email)

        signer = signers.SimpleSigner.load_pkcs1(
            key_pem=key_pem,
            cert_pem=cert_pem,
        )

        with open(self.pdf_path, "rb") as inf:
            pdf_reader = IncrementalPdfFileWriter(inf)
            output = signers.sign_pdf(
                pdf_out=pdf_reader,
                signer=signer,
                field_name="Signature1",
                existing_fields_only=False,
                new_field_spec=SigFieldSpec(sig_field_name="Signature1")
            )

        signed_path = f"outputs/signed_{genIdByEmail(self.email)}.pdf"
        with open(signed_path, "wb") as out:
            out.write(output.getbuffer())

        return signed_path
