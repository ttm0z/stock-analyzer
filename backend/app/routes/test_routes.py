from flask import Blueprint, request, jsonify
from ..db import db
from ..models.models import TestMessage
from ..utils.validation import InputValidator, ValidationError, handle_validation_error

test_bp = Blueprint('test', __name__)

@test_bp.route('/test')
def test():
    return jsonify({"message": "Hello from Flask!"})


@test_bp.route('/message', methods=['POST'])
@handle_validation_error
def save_message():
    print("saving message . . . ")
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    content = data.get('message')
    
    try:
        # Validate and sanitize message content
        validated_content = InputValidator.sanitize_message_content(content)
        
        new_msg = TestMessage(content=validated_content)
        db.session.add(new_msg)
        db.session.commit()

        return jsonify({'message': 'Message saved successfully!'}), 201
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500