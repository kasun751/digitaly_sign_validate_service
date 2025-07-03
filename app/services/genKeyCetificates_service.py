from cryptography.hazmat._oid import ExtendedKeyUsageOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.x509 import BasicConstraints, KeyUsage, ExtendedKeyUsage
from datetime import datetime, timedelta
from ..utils import genIdByEmail
import os


def generate_cert(subject_name, issuer_name, public_key, issuer_key, is_ca=False):
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject_name)
        .issuer_name(issuer_name)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(BasicConstraints(ca=is_ca, path_length=None), critical=True)
        .add_extension(KeyUsage(
            digital_signature=True,
            content_commitment=True,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=is_ca,
            crl_sign=is_ca,
            encipher_only=False,
            decipher_only=False
        ), critical=True)
    )

    if not is_ca:
        builder = builder.add_extension(
            ExtendedKeyUsage([ExtendedKeyUsageOID.CODE_SIGNING]),
            critical=False
        )

    return builder.sign(private_key=issuer_key, algorithm=hashes.SHA256())


class CertificateAuthorityService:
    def __init__(self, output_dir, country, state, locality, signer_email, organization, signer_cn,
                 root_cn="Root CA", intermediate_cn="Intermediate CA"):
        self.output_dir = output_dir
        self.country = country
        self.state = state
        self.locality = locality
        self.organization = organization
        self.root_cn = root_cn
        self.intermediate_cn = intermediate_cn
        self.signer_cn = signer_cn
        self.signer_email = signer_email
        self.unique_id = genIdByEmail(signer_email)
        os.makedirs(self.output_dir, exist_ok=True)

    def build_name(self, common_name):
        """Fixed typo in country attribute name"""
        return x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),  # Fixed typo here
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, self.signer_email)  # Ensure email is included
        ])

    def save_key(self, key, filename):
        key_path = os.path.join(self.output_dir, filename)
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        os.chmod(key_path, 0o600)  # Secure file permissions

    def save_cert(self, cert, filename):
        cert_path = os.path.join(self.output_dir, filename)
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        os.chmod(cert_path, 0o644)

    def generate_all(self):
        # Root CA
        root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        root_subject = self.build_name(self.root_cn)
        root_cert = generate_cert(root_subject, root_subject, root_key.public_key(), root_key, is_ca=True)
        self.save_key(root_key, f"root_key_{self.unique_id}.pem")
        self.save_cert(root_cert, f"root_cert_{self.unique_id}.pem")

        # Intermediate CA
        intermediate_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        intermediate_subject = self.build_name(self.intermediate_cn)
        intermediate_cert = generate_cert(
            intermediate_subject, root_subject,
            intermediate_key.public_key(), root_key, is_ca=True
        )
        self.save_key(intermediate_key, f"intermediate_key_{self.unique_id}.pem")
        self.save_cert(intermediate_cert, f"intermediate_cert_{self.unique_id}.pem")

        # Signer Certificate - Enhanced for document signing
        signer_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        signer_subject = self.build_name(self.signer_cn)
        signer_cert = generate_cert(
            signer_subject, intermediate_subject,
            signer_key.public_key(), intermediate_key, is_ca=False
        )
        self.save_key(signer_key, f"private_key_{self.unique_id}.pem")
        self.save_cert(signer_cert, f"cert_{self.unique_id}.pem")

        # CA Chain - Proper order (signer -> intermediate -> root)
        with open(os.path.join(self.output_dir, f"ca_chain_{self.unique_id}.pem"), "wb") as f:
            f.write(intermediate_cert.public_bytes(serialization.Encoding.PEM))
            f.write(root_cert.public_bytes(serialization.Encoding.PEM))

        # Return paths to generated files
        return {
            "private_key": os.path.join(self.output_dir, f"private_key_{self.unique_id}.pem"),
            "certificate": os.path.join(self.output_dir, f"cert_{self.unique_id}.pem"),
            "ca_chain": os.path.join(self.output_dir, f"ca_chain_{self.unique_id}.pem")
        }
# Example usage
if __name__ == "__main__":
    ca = CertificateAuthorityService(
        output_dir="pemFiles",
        country="LK",
        state="North Western Province",
        locality="Sri lankan",
        organization="My Company",
        root_cn="Root CA",
        intermediate_cn="Intermediate CA",
        signer_cn="kasun.com",
        signer_email="rkcp854@gmail.com"
    )
    ca.generate_all()
