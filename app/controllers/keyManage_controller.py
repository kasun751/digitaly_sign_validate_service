from flask import request, jsonify
from ..utils import getTokenData
from app.services.genKeyCetificates_service import CertificateAuthorityService
import hvac
import os
from dotenv import load_dotenv

load_dotenv()


def generateKeys():
    payload = getTokenData()

    if not payload["status"]:
        return jsonify(payload), 404

    # Token data
    userName = payload["userName"]
    signer_email = payload["signer_email"]

    # Setup Vault client
    VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

    if not client.is_authenticated():
        return jsonify({"error": "Vault authentication failed"}), 500

    try:
        # Initialize the certificate service
        cert_service = CertificateAuthorityService(
            country="LK",
            state="Uva Province",
            locality="Sri Lankan",
            organization="Uva Wellassa University",
            signer_cn=userName,
            signer_email=signer_email,
            vault_client=client,
            vault_base_path="secret/certs"
        )

        # Generate and store certificates in Vault
        result_paths = cert_service.generate_all()

        return jsonify({
            "message": "Successfully created and stored in Vault",
            "vault_paths": result_paths
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
