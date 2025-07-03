from flask import request, jsonify
from app.utils import jwtTokenValidator


def getTokenData():
    auth_header = request.headers.get('Authorization')
    validateResponse = jwtTokenValidator(auth_header)

    if validateResponse["status"]:
        userId = validateResponse["payload"]["userId"]
        userName = validateResponse["payload"]["userName"]
        signer_email = validateResponse["payload"]["email"]

        return {"UserId": userId, "userName": userName, "signer_email": signer_email,
                "status": validateResponse["status"]}
    else:
        return jsonify(validateResponse), 404
