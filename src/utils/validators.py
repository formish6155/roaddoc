import re
from typing import Optional, Tuple

def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    # Поддержка форматов: +79991234567, 89991234567, 9991234567
    pattern = r'^(\+?7|8)?\d{10}$'
    return bool(re.match(pattern, re.sub(r'\D', '', phone)))

def validate_coordinates(lat: float, lon: float) -> bool:
    """Валидация географических координат"""
    return -90 <= lat <= 90 and -180 <= lon <= 180

def extract_address_from_text(text: str) -> Optional[str]:
    """Извлечение адреса из текста (упрощённая версия)"""
    # Ищем паттерны, похожие на адреса
    patterns = [
        r'г\.\s*[\w\s]+',
        r'ул\.\s*[\w\s]+',
        r'пр\.\s*[\w\s]+',
        r'просп\.\s*[\w\s]+',
        r'д\.\s*\d+',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Очистка и ограничение длины текста"""
    # Удаляем потенциально опасные символы
    sanitized = re.sub(r'[<>]', '', text)
    return sanitized[:max_length]