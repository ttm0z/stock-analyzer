from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from ..models import Trade, db
import yfinance as yf
import pandas as pd
from flask import Blueprint, request, jsonify
from ..db import db
from ..models import TestMessage
from app.services.stock_service import fetch_stock_data, fetch_search_query


stock_bp = Blueprint('api', __name__)


@stock_bp.route('stock/<symbol>', methods=['GET'])
def get_stock(symbol):
    data = fetch_stock_data(symbol)
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Failed to fetch stock data'}), 500

@stock_bp.route('search/<symbol>', methods=['GET'])
def get_search_result(symbol):
    data = fetch_search_query(symbol)
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Failed to fetch search result'}), 500



@stock_bp.route('/api/price/<ticker>', methods=['GET'])
def get_price(ticker):
    data = yf.download(ticker, period='1mo')
    json_data = data.reset_index().to_dict(orient='records')
    return jsonify(json_data)



@stock_bp.route('/api/trade', methods=['POST'])
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
