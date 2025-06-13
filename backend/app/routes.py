from flask import Blueprint, request, jsonify
from .models import Trade, db
import yfinance as yf
import pandas as pd

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/price/<ticker>', methods=['GET'])
def get_price(ticker):
    data = yf.download(ticker, period='1mo')
    json_data = data.reset_index().to_dict(orient='records')
    return jsonify(json_data)


@api_bp.route('/api/test')
def test():
    return jsonify({"message": "Hello from Flask!"})

@api_bp.route('/api/trade', methods=['POST'])
def add_trade():
    data = request.get_json()
    trade = Trade(
        ticker=data['ticker'],
        date=data['date'],
        price=data['price'],
        quantity=data['quantity'],
        trade_type=data['trade_type']
    )
    db.session.add(trade)
    db.session.commit()
    return jsonify({"message": "Trade added"}), 201
