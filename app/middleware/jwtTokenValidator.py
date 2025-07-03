import jwt
from flask import Flask, request, jsonify, g
from werkzeug.wrappers import Request, Response

SECRET_KEY = "kasun1234"


class JwtTokenValidatorMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request_obj = Request(environ)
        print("🔍 Headers received by middleware:")
        for key, value in request_obj.headers.items():
            print(f"{key}: {value}")
        # request_obj = Request(environ)
        # auth_header = request_obj.headers.get('Authorization')
        #
        # if auth_header and auth_header.startswith("Bearer "):
        #     token = auth_header.split(" ")[1]
        #     try:
        #         decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        #         environ['user_payload'] = decoded  # attach to environ
        #     except jwt.ExpiredSignatureError:
        #         res = Response('{"error":"Token expired"}', status=401, mimetype='application/json')
        #         return res(environ, start_response)
        #     except jwt.InvalidTokenError:
        #         res = Response({"error": auth_header}, status=401, mimetype='application/json')
        #         return res(environ, start_response)
        # else:
        #     # If Authorization header is missing or malformed
        #     if request_obj.path.startswith("/secure"):  # Protect specific paths
        #         res = Response('{"error":"Authorization header missing or malformed"}',
        #                        status=401, mimetype='application/json')
        #         return res(environ, start_response)

        return self.app(environ, start_response)
