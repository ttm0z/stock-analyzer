from flask import Blueprint, request, jsonify
from ..db import db

from ..utils.validation import InputValidator, ValidationError, handle_validation_error

test_bp = Blueprint('test', __name__)

@test_bp.route('/test')
def test():
    return jsonify({"message": "Hello from Flask!"})
