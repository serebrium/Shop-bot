import re
from typing import Optional


def validate_price(price: str) -> Optional[int]:
    """Валидация цены товара"""
    try:
        price_int = int(price)
        if price_int <= 0 or price_int > 1000000:
            return None
        return price_int
    except ValueError:
        return None


def validate_text_input(text: str, max_length: int = 1000) -> Optional[str]:
    """Валидация текстового ввода"""
    if not text or len(text) > max_length:
        return None
    cleaned = re.sub("[<>\"'&]", "", text)
    return cleaned.strip()


def validate_callback_data(data: str, expected_prefix: str) -> Optional[str]:
    """Валидация callback_data"""
    if not data or not data.startswith(expected_prefix):
        return None
    return data
