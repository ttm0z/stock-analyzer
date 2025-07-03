import os
import requests
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
API_KEY = os.getenv("FMP_API_KEY")

def fetch_stock_data(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None


def fetch_search_query(keyword):
    url = f'https://financialmodelingprep.com/api/v3/search?query={keyword}&limit=10&apikey={API_KEY}'    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None
