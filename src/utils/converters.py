import re


def parse_participant(text: str) -> dict:
    """Данные участника ДТП: поля через запятую или каждое с новой строки"""
    parts = [p.strip() for p in re.split(r'[,\n]', text) if p.strip()]
    keys = ('name', 'phone', 'license_plate', 'insurance')
    return {key: parts[i] if i < len(parts) else 'Не указано' for i, key in enumerate(keys)}
