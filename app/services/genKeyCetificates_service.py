from cryptography.hazmat._oid import ExtendedKeyUsageOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.x509 import BasicConstraints, KeyUsage, ExtendedKeyUsage
from datetime import datetime, timedelta
from ..utils import genIdByEmail
import hvac


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
    def __init__(self, country, state, locality, signer_email, organization, signer_cn,
                 vault_client, vault_base_path="secret/certs",
                 root_cn="Root CA", intermediate_cn="Intermediate CA"):
        self.country = country
        self.state = state
        self.locality = locality
        self.organization = organization
        self.root_cn = root_cn
        self.intermediate_cn = intermediate_cn
        self.signer_cn = signer_cn
        self.signer_email = signer_email
        self.unique_id = genIdByEmail(signer_email)
        self.vault_client = vault_client
        self.vault_base_path = vault_base_path

    def build_name(self, common_name):
        return x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, self.signer_email)
        ])

    def store_in_vault(self, key: str, value: bytes):
        path = f"{self.vault_base_path}/{self.unique_id}/{key}"
        self.vault_client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret={"content": value.decode("utf-8")}
        )

    def generate_all(self):
        # Root CA
        root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        root_subject = self.build_name(self.root_cn)
        root_cert = generate_cert(root_subject, root_subject, root_key.public_key(), root_key, is_ca=True)
        self.store_in_vault("root_key", root_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        self.store_in_vault("root_cert", root_cert.public_bytes(serialization.Encoding.PEM))

        # Intermediate CA
        intermediate_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        intermediate_subject = self.build_name(self.intermediate_cn)
        intermediate_cert = generate_cert(
            intermediate_subject, root_subject,
            intermediate_key.public_key(), root_key, is_ca=True
        )
        self.store_in_vault("intermediate_key", intermediate_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        self.store_in_vault("intermediate_cert", intermediate_cert.public_bytes(serialization.Encoding.PEM))

        # Signer Certificate
        signer_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        signer_subject = self.build_name(self.signer_cn)
        signer_cert = generate_cert(
            signer_subject, intermediate_subject,
            signer_key.public_key(), intermediate_key, is_ca=False
        )
        self.store_in_vault("signer_key", signer_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        self.store_in_vault("signer_cert", signer_cert.public_bytes(serialization.Encoding.PEM))

        # CA Chain - concatenated intermediate + root certs
        ca_chain = (
            intermediate_cert.public_bytes(serialization.Encoding.PEM) +
            root_cert.public_bytes(serialization.Encoding.PEM)
        )
        self.store_in_vault("ca_chain", ca_chain)

        # Return Vault paths (informational)
        return {
            "private_key": f"{self.vault_base_path}/{self.unique_id}/signer_key",
            "certificate": f"{self.vault_base_path}/{self.unique_id}/signer_cert",
            "ca_chain": f"{self.vault_base_path}/{self.unique_id}/ca_chain"
        }
