
from src.valuation.valuation import ValuationEngine
import logging
from src.config.api_data import CurrentData
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

data=CurrentData()
def test_price():
    engine = ValuationEngine()
    symbol = "TCS"

    print(f"--- Testing Price Fetch for {symbol} ---")
    price = engine._data.get_current_price(symbol)
    print(f"FINAL RESULT: {price}")

if __name__ == "__main__":
    test_price()