import os
import hvac
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from cryptography import x509

load_dotenv()

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
KEY_PATH = os.getenv("VAULT_KEY_PATH", "secret/certificates/signing-key")

client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

if not client.is_authenticated():
    raise RuntimeError("Vault authentication failed.")


def store_pem(path, pem_bytes: bytes):
    client.secrets.kv.v2.create_or_update_secret(
        path=path,
        secret={"pem": pem_bytes.decode()}
    )


def read_pem(path) -> bytes:
    resp = client.secrets.kv.v2.read_secret_version(path=path)
    return resp['data']['data']['pem'].encode()


def load_private_key_and_cert():
    try:
        secret = client.secrets.kv.v2.read_secret_version(path=KEY_PATH)
        private_key_pem = secret['data']['data']['private_key']
        cert_pem = secret['data']['data']['certificate']

    except hvac.exceptions.InvalidPath:
        # Not found in Vault – generate and store
        from app.controllers.keyManage_controller import generateKeys
        private_key_pem, cert_pem = generateKeys()

        # Store to Vault
        client.secrets.kv.v2.create_or_update_secret(
            path=KEY_PATH,
            secret={
                "private_key": private_key_pem,
                "certificate": cert_pem,
            }
        )

    # Parse PEM strings into objects
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
    )
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    return private_key, cert
