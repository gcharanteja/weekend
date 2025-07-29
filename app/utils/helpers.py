from typing import Dict, Any
import json

def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format"""
    # Implement actual symbol validation logic
    return len(symbol) > 0 and "-" in symbol

def normalize_market_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize market data to a consistent format"""
    return {
        'symbol': data.get('tradingsymbol', ''),
        'exchange': data.get('exchange', ''),
        'ltp': float(data.get('ltp', 0)),
        'volume': int(data.get('volume', 0)),
        'timestamp': data.get('timestamp', '')
    }

def load_json_config(file_path: str) -> Dict[str, Any]:
    """Load JSON configuration file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Error loading config file {file_path}: {str(e)}")