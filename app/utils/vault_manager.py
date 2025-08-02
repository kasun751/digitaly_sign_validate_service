import os
import hvac
from dotenv import load_dotenv

load_dotenv()

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
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
