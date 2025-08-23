import hvac
from cryptography.hazmat._oid import ExtendedKeyUsageOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.x509 import BasicConstraints, KeyUsage, ExtendedKeyUsage
from datetime import datetime, timedelta
from ..utils import genIdByEmail
import os
import logging

logger = logging.getLogger(__name__)


# -----------------
# Vault Connection
# -----------------
def get_vault_client():
    vault_addr = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    vault_token = os.getenv("VAULT_TOKEN")
    print(f"[DEBUG] Connecting to Vault at {vault_addr}")
    if not vault_token:
        raise ValueError("VAULT_TOKEN environment variable not set!")

    client = hvac.Client(url=vault_addr, token=vault_token)
    if not client.is_authenticated():
        raise ValueError("Vault authentication failed!")
    print("[DEBUG] Vault authentication successful")
    return client


# -----------------
# Cert Generation
# -----------------
def generate_cert(subject_name, issuer_name, public_key, issuer_key, is_ca=False):
    print(f"[DEBUG] Generating certificate for {subject_name.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value}")
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

    cert = builder.sign(private_key=issuer_key, algorithm=hashes.SHA256())
    print(
        f"[DEBUG] Certificate generated successfully for {subject_name.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value}")
    return cert


# -----------------
# Certificate Service
# -----------------
class CertificateAuthorityService:
    def __init__(self, vault_base_path, country, state, locality, signer_email,
                 organization, signer_cn, root_cn="Root CA", intermediate_cn="Intermediate CA"):
        self.vault_base_path = vault_base_path.rstrip("/")
        self.country = country
        self.state = state
        self.locality = locality
        self.organization = organization
        self.root_cn = root_cn
        self.intermediate_cn = intermediate_cn
        self.signer_cn = signer_cn
        self.signer_email = signer_email
        self.unique_id = genIdByEmail(signer_email)
        print(f"[DEBUG] Unique ID for signer: {self.unique_id}")
        self.client = get_vault_client()

    def build_name(self, common_name):
        print(f"[DEBUG] Building X.509 name for {common_name}")
        return x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, self.signer_email)
        ])

    def store_in_vault(self, name, pem_bytes):
        """Store PEM data securely in Vault using KV v2"""
        pem_str = pem_bytes.decode("utf-8")
        vault_path = f"{self.unique_id}/{name}"  # KV v2 path is relative to mount
        print(f"[DEBUG] Storing {name} at {self.vault_base_path}/data/{vault_path}")
        self.client.secrets.kv.v2.create_or_update_secret(
            path=vault_path,
            secret={"value": pem_str},
            mount_point=self.vault_base_path  # Specify mount point explicitly
        )
        print(f"[DEBUG] Stored {name} successfully")

    def generate_all(self):
        print("[DEBUG] Start key generation")

        # Root CA
        root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        print("[DEBUG] Root key generated")
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
        print("[DEBUG] Intermediate key generated")
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
        print("[DEBUG] Signer key generated")
        signer_subject = self.build_name(self.signer_cn)
        signer_cert = generate_cert(
            signer_subject, intermediate_subject,
            signer_key.public_key(), intermediate_key, is_ca=False
        )

        self.store_in_vault("private_key", signer_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        self.store_in_vault("cert", signer_cert.public_bytes(serialization.Encoding.PEM))

        # CA Chain
        ca_chain_pem = (
                intermediate_cert.public_bytes(serialization.Encoding.PEM) +
                root_cert.public_bytes(serialization.Encoding.PEM)
        )
        self.store_in_vault("ca_chain", ca_chain_pem)
        print("[DEBUG] CA chain stored successfully")

        print("[DEBUG] All keys and certificates generated and stored successfully")
        return {
            "private_key": f"{self.vault_base_path}/{self.unique_id}/private_key",
            "certificate": f"{self.vault_base_path}/{self.unique_id}/cert",
            "ca_chain": f"{self.vault_base_path}/{self.unique_id}/ca_chain"
        }
