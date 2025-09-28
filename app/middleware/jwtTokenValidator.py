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

        return self.app(environ, start_response)
