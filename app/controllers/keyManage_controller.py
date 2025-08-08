from flask import request, jsonify
from ..utils import getTokenData
from app.services import CertificateAuthorityService


def generateKeys():
    payload = getTokenData()

    if payload["status"]:
        userName = payload["userName"]
        signer_email = payload["signer_email"]

        genKeyService = CertificateAuthorityService(
            vault_base_path="certs",  # Store under Vault path
            country="LK",
            state="Uva Province",
            locality="Sri Lankan",
            organization="Uva Wellassa University",
            root_cn="Root CA",
            intermediate_cn="Intermediate CA",
            signer_cn=userName,
            signer_email=signer_email
        )

        genKeyService.generate_all()
        return jsonify({"message": "Successfully created"}), 201
    else:
        return jsonify(payload), 404
