import re

def validate_coordinates(lat: float, lon: float) -> bool:
    """Валидация географических координат"""
    return -90 <= lat <= 90 and -180 <= lon <= 180

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Очистка и ограничение длины текста"""
    # Удаляем потенциально опасные символы
    sanitized = re.sub(r'[<>]', '', text)
    return sanitized[:max_length]