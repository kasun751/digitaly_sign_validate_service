from flask import Blueprint, request, jsonify
from app.controllers import generateKeys

keys_bp = Blueprint("keys_bp", __name__)


@keys_bp.route('/generateKeys', methods=['POST'])
def initializeKeys():
    return generateKeys()
