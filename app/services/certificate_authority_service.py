from app.vault_client import VaultClient
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class CertificateAuthorityService:
    def __init__(self):
        self.vault = VaultClient()

    def generate_and_store_keys(self, username: str):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Store in Vault
        self.vault.store_secret(f"certs/{username}/private_key", private_pem.decode())
        self.vault.store_secret(f"certs/{username}/public_key", public_pem.decode())

        return {
            "private_key": private_pem.decode(),
            "public_key": public_pem.decode()
        }

    def get_private_key(self, username: str):
        pem = self.vault.read_secret(f"certs/{username}/private_key")
        if pem:
            return serialization.load_pem_private_key(pem.encode(), password=None)
        return None

    def get_public_key(self, username: str):
        pem = self.vault.read_secret(f"certs/{username}/public_key")
        if pem:
            return serialization.load_pem_public_key(pem.encode())
        return None
