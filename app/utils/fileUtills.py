import os
import requests
import uuid
import tempfile
import hvac
import logging
from firebase_admin import storage
from .generateIdByEmail import genIdByEmail

logger = logging.getLogger(__name__)


# Vault client factory (use env vars)
def get_vault_client():
    vault_addr = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    vault_token = os.getenv("VAULT_TOKEN")
    if not vault_token:
        raise EnvironmentError("VAULT_TOKEN environment variable not set")
    client = hvac.Client(url=vault_addr, token=vault_token)
    if not client.is_authenticated():
        raise EnvironmentError("Vault authentication failed")
    return client


def checkFileAvailability(path):
    if path is None:
        return None
    return os.path.isfile(path)


def removeUnWantedFiles(path):
    if not path:
        return None
    try:
        if os.path.isfile(path):
            os.remove(path)
            logger.debug("Removed file: %s", path)
            return True
    except Exception as e:
        logger.exception("Failed to remove file %s: %s", path, e)
    return False


def download_pdf_from_url(url):
    try:
        unique_filename = f"temp_{uuid.uuid4().hex}.pdf"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        os.makedirs("temp_download", exist_ok=True)
        file_path = os.path.join("temp_download", unique_filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    except Exception as e:
        logger.exception("Error downloading PDF: %s", e)
        return None

# Check certificate availability
def findCertAvailability(signer_email, vault_base_path="certs"):
    if not signer_email:
        return None, "signer_email required"

    client = get_vault_client()
    signerId = genIdByEmail(signer_email)

    cert_files = {
        "privateKey": "private_key",
        "caChain": "ca_chain",
        "intermediateCert": "intermediate_cert",
        "root_cert": "root_cert",
        "rootKey": "root_key",
        "cert": "cert"
    }

    missing = []
    for key, value in cert_files.items():
        try:
            secret = client.secrets.kv.v2.read_secret_version(
                path=f"{signerId}/{value}",
                mount_point=vault_base_path
            )
            pem_val = secret.get("data", {}).get("data", {}).get("value")
            if not pem_val:
                missing.append(value)
        except hvac.exceptions.InvalidPath:
            missing.append(value)
        except Exception as e:
            logger.exception("Vault read error for %s/%s: %s", signerId, value, e)
            missing.append(value)

    if missing:
        return False, missing
    return True, []

# Load certificates to temporary files
def load_certs_from_vault_to_temp(signer_email, vault_base_path="certs"):
    client = get_vault_client()
    signerId = genIdByEmail(signer_email)
    keys = ["private_key", "cert", "ca_chain", "root_cert", "root_key"]

    temp_paths = {}
    for key in keys:
        try:
            secret = client.secrets.kv.v2.read_secret_version(
                path=f"{signerId}/{key}",
                mount_point=vault_base_path
            )
            pem = secret.get("data", {}).get("data", {}).get("value")
            if not pem:
                raise FileNotFoundError(f"Missing {key} in Vault at {vault_base_path}/{signerId}/{key}")

            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
            tf.write(pem.encode("utf-8"))
            tf.flush()
            tf.close()
            temp_paths[key] = tf.name

        except Exception as e:
            logger.exception("Failed to load %s for %s: %s", key, signer_email, e)
            raise

    return temp_paths
