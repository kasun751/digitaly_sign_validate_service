import jwt

SECRET_KEY = "a-string-secret-at-least-256-bits-long"


def jwtTokenValidator(auth_header):
    jwtToken = auth_header.split(" ")[1]
    if not jwtToken:
        return {"error": "Authorization header missing"}

    try:
        # Decode without verifying to inspect the payload (debug only)
        decoded = jwt.decode(jwtToken, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})
        # Check the payload structure
        return {"message": "Access granted", "status": True, "payload": decoded}
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired", "status": False}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token test", "status": False}

# res = jwtTokenValidator("eyJhbGciOiJIUzI1NiJ9.eyJuYW1lIjoiS2FzdW4iLCJleHAiOjE3NDcwMzY2ODAsInVzZXJJZCI6IjEyMzQ1NiJ9.nsHcK6-Bg0iY3VwRb0KkAAV6L03jy0_ietYSYo0WQuc")
# print(res['payload']['name'])
