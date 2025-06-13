from flask import Blueprint, request, jsonify
from ..models import Trade, db
import yfinance as yf
import pandas as pd
from flask import Blueprint, request, jsonify
from ..db import db
from ..models import TestMessage

test_bp = Blueprint('test', __name__)

@test_bp.route('/test')
def test():
    return jsonify({"message": "Hello from Flask!"})


@test_bp.route('/message', methods=['POST'])
def save_message():
    print("saving message . . . ")
    data = request.get_json()
    content = data.get('message')
    if not content:
        return jsonify({'error': 'No message provided'}), 400

    new_msg = TestMessage(content=content)
    db.session.add(new_msg)
    db.session.commit()

    return jsonify({'message': 'Message saved successfully!'}), 201