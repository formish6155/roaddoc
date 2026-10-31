def parse_participant(text: str) -> dict:
    """Данные участника ДТП: поля через запятую или каждое с новой строки"""
    # Построчный ввод делим только по строкам, чтобы запятая внутри поля («СОГАЗ, полис …») его не дробила
    separator = '\n' if '\n' in text else ','
    parts = [p.strip() for p in text.split(separator) if p.strip()]
    keys = ('name', 'phone', 'license_plate', 'insurance')
    return {key: parts[i] if i < len(parts) else 'Не указано' for i, key in enumerate(keys)}
