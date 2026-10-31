from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from datetime import datetime, timezone
import json
from xml.sax.saxutils import escape
from src.config import settings

# Шрифт с кириллицей лежит в репозитории, чтобы PDF читался на любой ОС, а не только на macOS
FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
pdfmetrics.registerFont(TTFont('DejaVuSans', FONTS_DIR / "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONTS_DIR / "DejaVuSans-Bold.ttf"))
DEFAULT_FONT = 'DejaVuSans'
BOLD_FONT = 'DejaVuSans-Bold'

def _t(value) -> str:
    """Текст пользователя для Paragraph: reportlab читает < > & как разметку, и «<b>» без закрытия роняет сборку"""
    return escape(str(value))

def _created_at(data: dict) -> datetime:
    """Время создания из БД в местном времени (SQLite хранит UTC без часового пояса)"""
    created_at = data.get('created_at') or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return created_at.astimezone()

def _as_list(value) -> list:
    """Список из готового list или из JSON-строки (как хранится в БД)"""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, list) else []

def generate_problem_statement(report_data: dict) -> str:
    """
    Генерация заявления о проблеме на дороге в PDF
    
    Args:
        report_data: Словарь с данными отчёта
        
    Returns:
        Путь к сгенерированному PDF-файлу
    """
    # Создаём имя файла
    filename = f"report_{report_data['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = settings.DOCS_DIR / filename
    
    # Создаём документ
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Стили
    styles = getSampleStyleSheet()
    
    # Заголовок
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName=BOLD_FONT,
        fontSize=16,
        alignment=1,  # Центрирование
        spaceAfter=14
    )
    
    # Подзаголовок
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT,
        fontSize=12,
        alignment=1,
        spaceAfter=20
    )
    
    # Заголовок секции
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName=BOLD_FONT,
        fontSize=12,
        spaceAfter=6,
        textColor=colors.darkblue
    )
    
    # Обычный текст
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT,
        fontSize=11,
        spaceAfter=8,
        leading=14
    )
    
    # Мелкий текст (примечания)
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT,
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=6
    )
    
    # Элементы документа
    elements = []
    
    # Шапка документа
    elements.append(Paragraph("РОССИЙСКАЯ ФЕДЕРАЦИЯ", title_style))
    elements.append(Paragraph("СИСТЕМА ПРИЁМА ОБРАЩЕНИЙ ГРАЖДАН", subtitle_style))
    elements.append(Spacer(1, 10))
    
    # Заголовок
    elements.append(Paragraph("ЗАЯВЛЕНИЕ", title_style))
    elements.append(Paragraph("о проблеме на автомобильной дороге", subtitle_style))
    elements.append(Spacer(1, 12))
    
    # Данные заявителя
    elements.append(Paragraph("Данные заявителя:", section_header_style))
    elements.append(Paragraph(f"ФИО: {_t(report_data.get('user_full_name', 'Не указано'))}", normal_style))
    elements.append(Paragraph(f"Telegram: @{_t(report_data.get('username', report_data.get('telegram_id', 'N/A')))}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Информация о проблеме
    elements.append(Paragraph("Информация о проблеме:", section_header_style))
    elements.append(Paragraph(f"Тип проблемы: {report_data['problem_type']}", normal_style))
    
    if report_data.get('latitude') and report_data.get('longitude'):
        elements.append(Paragraph(
            f"Координаты: {report_data['latitude']:.6f}, {report_data['longitude']:.6f}",
            normal_style
        ))
    elif report_data.get('address'):
        elements.append(Paragraph(f"Адрес: {_t(report_data['address'])}", normal_style))
    
    if report_data.get('description'):
        elements.append(Paragraph("Описание проблемы:", section_header_style))
        elements.append(Paragraph(_t(report_data['description']), normal_style))
    
    elements.append(Spacer(1, 15))
    
    # Статус и дата
    elements.append(Paragraph(f"Статус обращения: Новое", normal_style))
    elements.append(Paragraph(f"Дата подачи: {_created_at(report_data).strftime('%d.%m.%Y %H:%M')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Подпись
    elements.append(Paragraph("_" * 40, normal_style))
    elements.append(Paragraph("(цифровая подпись заявителя)", small_style))
    elements.append(Spacer(1, 30))
    
    # Примечание
    elements.append(Paragraph(
        "Примечание: Данное заявление сформировано автоматически системой RoadDoc. "
        "Для подтверждения факта подачи заявления сохраните данный документ. "
        "Номер обращения: RD-{id}".format(id=report_data['id']),
        small_style
    ))
    
    # Генерация PDF с обработкой ошибок
    try:
        doc.build(elements)
        return str(filepath)
    except Exception as e:
        # Fallback: создаём простой текстовый файл если PDF не сгенерировался
        txt_path = filepath.with_suffix('.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("ЗАЯВЛЕНИЕ О ПРОБЛЕМЕ НА ДОРОГЕ\n")
            f.write("=" * 50 + "\n")
            f.write(f"Номер: RD-{report_data['id']}\n")
            f.write(f"Дата: {_created_at(report_data).strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"Тип проблемы: {report_data['problem_type']}\n")
            if report_data.get('address'):
                f.write(f"Адрес: {report_data['address']}\n")
            elif report_data.get('latitude'):
                f.write(f"Координаты: {report_data['latitude']:.6f}, {report_data['longitude']:.6f}\n")
            if report_data.get('description'):
                f.write(f"Описание: {report_data['description']}\n")
            f.write("\nСформировано системой RoadDoc")
        
        return str(txt_path)

def generate_accident_protocol(accident_data: dict) -> str:
    """
    Генерация европротокола ДТП в PDF
    
    Args:
        accident_data: Словарь с данными ДТП
        
    Returns:
        Путь к сгенерированному PDF-файлу
    """
    # Создаём имя файла
    filename = f"accident_{accident_data['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = settings.DOCS_DIR / filename
    
    # Создаём документ
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Стили
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName=BOLD_FONT,
        fontSize=18,
        alignment=1,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName=BOLD_FONT,
        fontSize=14,
        alignment=1,
        spaceAfter=20,
        textColor=colors.red
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName=BOLD_FONT,
        fontSize=12,
        spaceAfter=6,
        textColor=colors.darkblue
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT,
        fontSize=11,
        spaceAfter=8,
        leading=14
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT,
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=6
    )
    
    # Элементы документа
    elements = []
    
    # Заголовок
    elements.append(Paragraph("ЕВРОПРОТОКОЛ", title_style))
    elements.append(Paragraph("Извещение о дорожно-транспортном происшествии", subtitle_style))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("(без участия уполномоченных сотрудников полиции)", small_style))
    elements.append(Spacer(1, 15))
    
    # Место и время ДТП
    elements.append(Paragraph("Место и время происшествия:", section_header_style))
    
    location_info = []
    if accident_data.get('latitude') and accident_data.get('longitude'):
        location_info.append(f"Координаты: {accident_data['latitude']:.6f}, {accident_data['longitude']:.6f}")
    location_info.append(f"Дата и время: {_created_at(accident_data).strftime('%d.%m.%Y %H:%M')}")
    
    for line in location_info:
        elements.append(Paragraph(line, normal_style))
    
    elements.append(Spacer(1, 12))
    
    # Участники ДТП
    elements.append(Paragraph("Участники ДТП:", section_header_style))
    
    participants = _as_list(accident_data.get('participants'))
    
    if not participants:
        elements.append(Paragraph("Данные участников не указаны", normal_style))
    else:
        for i, participant in enumerate(participants, 1):
            elements.append(Paragraph(f"Участник №{i}:", section_header_style))
            elements.append(Paragraph(f"ФИО: {_t(participant.get('name', 'Не указано'))}", normal_style))
            elements.append(Paragraph(f"Телефон: {_t(participant.get('phone', 'Не указано'))}", normal_style))
            elements.append(Paragraph(f"Гос. номер: {_t(participant.get('license_plate', 'Не указано'))}", normal_style))
            elements.append(Paragraph(f"Страховая: {_t(participant.get('insurance', 'Не указано'))}", normal_style))
            elements.append(Spacer(1, 8))
    
    elements.append(Spacer(1, 12))
    
    # Обстоятельства ДТП
    elements.append(Paragraph("Обстоятельства ДТП:", section_header_style))
    description = accident_data.get('description', 'Не указано')
    elements.append(Paragraph(_t(description), normal_style))
    elements.append(Spacer(1, 12))
    
    # Количество фотографий
    photo_count = len(_as_list(accident_data.get('photo_paths')))
    
    elements.append(Paragraph(f"Приложено фотографий: {photo_count}", normal_style))
    elements.append(Spacer(1, 15))
    
    # Дата составления
    elements.append(Paragraph(f"Дата составления извещения: {_created_at(accident_data).strftime('%d.%m.%Y')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Подписи
    elements.append(Paragraph("Подписи участников ДТП:", section_header_style))
    elements.append(Spacer(1, 5))
    
    for i in range(max(2, len(participants))):
        elements.append(Paragraph(f"Участник №{i+1}: _________________________ / _________________________", normal_style))
        elements.append(Paragraph("(подпись)                          (расшифровка)", small_style))
        elements.append(Spacer(1, 8))
    
    elements.append(Spacer(1, 25))
    
    # Важное предупреждение
    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontName=BOLD_FONT,
        fontSize=10,
        textColor=colors.red,
        spaceAfter=10,
        alignment=1
    )
    
    elements.append(Paragraph("ВНИМАНИЕ!", warning_style))
    elements.append(Paragraph(
        "1. Данный документ является предварительным извещением.\n"
        "2. Обязательно уведомите страховую компанию в течение 5 рабочих дней.\n"
        "3. При наличии пострадавших или разногласий по обстоятельствам ДТП — незамедлительно вызовите ГИБДД (112).\n"
        "4. Сохраните все оригиналы документов и фотографии до завершения страхового случая.",
        normal_style
    ))
    
    # Генерация PDF с обработкой ошибок
    try:
        doc.build(elements)
        return str(filepath)
    except Exception as e:
        # Fallback в текстовый файл
        txt_path = filepath.with_suffix('.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("ЕВРОПРОТОКОЛ ДТП\n")
            f.write("=" * 50 + "\n")
            f.write(f"Номер ДТП: ACC-{accident_data['id']}\n")
            f.write(f"Дата: {_created_at(accident_data).strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"Участников: {len(participants)}\n")
            f.write(f"Обстоятельства: {accident_data.get('description', 'Не указано')}\n")
            f.write("\nСформировано системой RoadDoc")
            f.write("\n\nВАЖНО: При наличии пострадавших или разногласий — вызовите ГИБДД (112)!")
        
        return str(txt_path)