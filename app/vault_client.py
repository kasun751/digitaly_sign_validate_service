import hvac


class VaultClient:
    def __init__(self):
        self.client = hvac.Client(url='http://127.0.0.1:8200', token='your-root-token')  # Replace securely
        if not self.client.is_authenticated():
            raise Exception("Vault Authentication Failed")

    def get_certificate(self, email):
        path = f'secret/data/certs/{email}'
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']['certificate'].encode()

    def get_private_key(self, email):
        path = f'secret/data/keys/{email}'
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']['private_key'].encode()

    def store_certificate(self, email, cert_pem):
        path = f'secret/data/certs/{email}'
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret={"certificate": cert_pem.decode()}
        )

    def store_private_key(self, email, key_pem):
        path = f'secret/data/keys/{email}'
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret={"private_key": key_pem.decode()}
        )

    def store_cert_bundle(self, unique_id, private_key_pem, cert_pem, ca_chain_pem, root_cert_pem):
        self.client.secrets.kv.v2.create_or_update_secret(
            path=f"certs/{unique_id}",
            secret={
                "private_key": private_key_pem,
                "certificate": cert_pem,
                "ca_chain": ca_chain_pem,
                "root_cert": root_cert_pem
            }
        )

    def load_cert_bundle(self, unique_id):
        result = self.client.secrets.kv.v2.read_secret_version(path=f"certs/{unique_id}")
        return result["data"]["data"]
