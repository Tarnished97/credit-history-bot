import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
import pdfplumber

# ==============================
# НАСТРОЙКИ
# ==============================
BOT_TOKEN = "Ваш Токен"
MANAGER_TG = "@Tarnished97"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
os.makedirs("downloads", exist_ok=True)

user_states = {}
user_calc = {}
pdf_cache = {}

# ==============================
# БАЗА БАНКОВ (основные кредиты)
# ==============================
BANKS_DATA = {
    "Сбер Банк":        {"url": "https://www.sber-bank.by", "min_score": "E3", "sum_without_cert": "до 30 000 BYN", "sum_with_cert": "до 50 000 BYN", "rate": 17.65, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "Нео Банк":         {"url": "https://www.neobank.by", "min_score": "E3", "sum_without_cert": "до 30 000 BYN", "sum_with_cert": "до 50 000 BYN", "rate": 17.65, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "МТБанк":           {"url": "https://www.mtbank.by", "min_score": "E3", "sum_without_cert": "до 10 000 BYN", "sum_with_cert": "до 20 000 BYN", "rate": 24.99, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "Альфа-Банк":       {"url": "https://www.alfabank.by", "min_score": "Д3", "sum_without_cert": "до 10 000 BYN", "sum_with_cert": "до 15 000 BYN", "rate": 17.96, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "РРБ-Банк":         {"url": "https://www.rrb.by", "min_score": "Д3", "sum_without_cert": "до 30 000 BYN", "sum_with_cert": "до 70 000 BYN", "rate": 17.65, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "Беларусбанк":      {"url": "https://www.belarusbank.by", "min_score": "D2/D3", "sum_without_cert": "до 10 000 BYN", "sum_with_cert": "до 13 500 BYN", "rate": 17.96, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "Технобанк":        {"url": "https://www.technobank.by", "min_score": "E3", "sum_without_cert": "до 30 000 BYN", "sum_with_cert": "до 30 000 BYN", "rate": 17.96, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "Белагропромбанк":  {"url": "https://www.belagroprombank.com", "min_score": "E3", "sum_without_cert": "до 35 000 BYN", "sum_with_cert": "до 35 000 BYN", "rate": 23.00, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "Банк Решение":     {"url": "https://www.solutionbank.by", "min_score": "E2", "sum_without_cert": "до 50 000 BYN", "sum_with_cert": "до 50 000 BYN", "rate": 17.96, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "БНБ-Банк":         {"url": "https://www.bnb.by", "min_score": "Д3", "sum_without_cert": "до 20 000 BYN", "sum_with_cert": "до 40 000 BYN", "rate": 17.65, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "БТБ":              {"url": "https://www.btb.by", "min_score": "Д3", "sum_without_cert": "до 30 000 BYN", "sum_with_cert": "до 30 000 BYN", "rate": 22.9, "term_months": 60, "term": "до 5 лет", "payment_type": "Д"},
    "Статусбанк":       {"url": "https://www.statusbank.by", "min_score": "Д3", "sum_without_cert": "до 10 000 BYN", "sum_with_cert": "до 20 000 BYN", "rate": 25.0, "term_months": 48, "term": "до 4 лет", "payment_type": "А"},
    "Дабрабыт":         {"url": "https://www.dabrabyt.by", "min_score": "Д1", "sum_without_cert": "до 30 000 BYN", "sum_with_cert": "до 50 000 BYN", "rate": 17.96, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "Цептер Банк":      {"url": "https://www.zepterbank.by", "min_score": "Д3", "sum_without_cert": "до 10 000 BYN", "sum_with_cert": "до 15 000 BYN", "rate": 17.50, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "Паритетбанк":      {"url": "https://www.paritetbank.by", "min_score": "Д2", "sum_without_cert": "до 20 000 BYN", "sum_with_cert": "до 100 000 BYN", "rate": 17.96, "term_months": 60, "term": "до 5 лет", "payment_type": "Д"},
    "БелВЭБ":           {"url": "https://www.belveb.by", "min_score": "Д1", "sum_without_cert": "до 100 000 BYN", "sum_with_cert": "до 100 000 BYN", "rate": 16.90, "term_months": 84, "term": "до 7 лет", "payment_type": "А"},
    "Приорбанк":        {"url": "https://www.priorbank.by", "min_score": "E3", "sum_without_cert": "до 20 000 BYN", "sum_with_cert": "до 70 000 BYN", "rate": 17.45, "term_months": 60, "term": "до 5 лет", "payment_type": "А"},
    "ВТБ (Беларусь)":   {"url": "https://www.vtb.by", "min_score": "E3", "sum_without_cert": "до 50 000 BYN", "sum_with_cert": "до 70 000 BYN", "rate": 24.9, "term_months": 84, "term": "до 7 лет", "payment_type": "А"},
    "Белинвестбанк":    {"url": "https://www.belinvestbank.by", "min_score": "E3", "sum_without_cert": "до 10 000 BYN", "sum_with_cert": "до 20 000 BYN", "rate": 17.45, "term_months": 60, "term": "до 5 лет", "payment_type": "Д"},
}

BANK_KEYS = list(BANKS_DATA.keys())

# ==============================
# БАЗА БАНКОВ (рефинансирование)
# ==============================
BANKS_REFINANCE = {
    "Дабрабыт":      {"rate": 22.0,  "max_sum": 50000, "term_months": 60, "docs": "none",   "url": "https://www.dabrabyt.by"},
    "Сбер Банк":     {"rate": 17.65, "max_sum": 55000, "term_months": 84, "docs": "none",   "url": "https://www.sber-bank.by"},
    "Белагропромбанк": {"rate": 19.1, "max_sum": 35000, "term_months": 84, "docs": "light", "url": "https://www.belagroprombank.com"},
    "БелВЭБ":        {"rate": 17.96, "max_sum": 100000, "term_months": 84, "docs": "light", "url": "https://www.belveb.by"},
    "РРБ-Банк":      {"rate": 19.1,  "max_sum": 10000, "term_months": 36, "docs": "light", "url": "https://www.rrb.by"},
    "Альфа-Банк":    {"rate": 18.18, "max_sum": 20000, "term_months": 60, "docs": "light", "url": "https://www.alfabank.by"},
    "Технобанк":     {"rate": 17.9,  "max_sum": 25000, "term_months": 84, "docs": "light", "url": "https://www.technobank.by"},
    "Статусбанк":    {"rate": 17.0,  "max_sum": 20000, "term_months": 60, "docs": "light", "url": "https://www.statusbank.by"},
    "Банк Решение":  {"rate": 18.92, "max_sum": 50000, "term_months": 60, "docs": "light", "url": "https://www.solutionbank.by"},
    "Нео Банк":      {"rate": 18.18, "max_sum": 50000, "term_months": 60, "docs": "light", "url": "https://www.neobank.by"},
    "Цептер Банк":   {"rate": 16.50, "max_sum": 15000, "term_months": 60, "docs": "light", "url": "https://www.zepterbank.by"},
    "БНБ-Банк":      {"rate": 17.50, "max_sum": 50000, "term_months": 84, "docs": "light", "url": "https://www.bnb.by"},
    "Белинвестбанк": {"rate": 18.49, "max_sum": 30000, "term_months": 60, "docs": "light", "url": "https://www.belinvestbank.by"},
    "Беларусбанк":   {"rate": 17.5,  "max_sum": 35000, "term_months": 84, "docs": "heavy", "url": "https://www.belarusbank.by"},
    "МТБанк":        {"rate": 24.99, "max_sum": 40000, "term_months": 60, "docs": "none",   "url": "https://www.mtbank.by"},
}

# ==============================
# СКРЫТЫЕ ФИЛЬТРЫ
# ==============================
HIDDEN_FILTERS = {
    "no_kids_deduction": ["ВТБ (Беларусь)", "БНБ-Банк", "Беларусбанк", "Белагропромбанк",
                          "Альфа-Банк", "Паритетбанк", "РРБ-Банк", "Статусбанк",
                          "Технобанк", "Приорбанк", "Дабрабыт"],
    "no_fszn_check": ["Нео Банк", "Альфа-Банк", "БТБ", "Дабрабыт", "Цептер Банк", "МТБанк"],
    "loyal_to_mfo": ["Приорбанк", "Белагропромбанк", "Беларусбанк", "Статусбанк",
                     "Цептер Банк", "Альфа-Банк", "РРБ-Банк"],
    "loyal_to_exec": ["Сбер Банк", "Альфа-Банк", "МТБанк", "БелВЭБ", "Статусбанк"],
    "age_18_20": ["Беларусбанк", "МТБанк", "Сбер Банк", "Белагропромбанк",
                  "Дабрабыт", "БНБ-Банк", "Белинвестбанк", "Паритетбанк"],
    "age_65_plus": ["Сбер Банк", "ВТБ (Беларусь)", "РРБ-Банк", "Статусбанк",
                    "Технобанк", "Беларусбанк", "Дабрабыт", "БелВЭБ", "МТБанк",
                    "Альфа-Банк", "Нео Банк", "БНБ-Банк"],
    "self_employed": ["ВТБ (Беларусь)", "Беларусбанк", "Белагропромбанк"],
    "ignore_ki_requests": ["Нео Банк", "МТБанк", "Альфа-Банк", "РРБ-Банк",
                           "БНБ-Банк", "БТБ", "Белинвестбанк", "Приорбанк"],
}

SCORE_ORDER = {
    "A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6,
    "D1": 7, "D2": 8, "D3": 9, "E1": 10, "E2": 11, "E3": 12, "F": 13
}

# ==============================
# PDF ПАРСИНГ
# ==============================
def extract_text_from_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)

def extract_user_score(text: str):
    idx = text.lower().find("класс рейтинга")
    if idx != -1:
        segment = text[idx:idx + 800]
        m = re.search(r"\b([A-F][1-3])\b", segment)
        if m:
            return m.group(1).upper()
        m = re.search(r"\b(F)\b", segment)
        if m:
            return "F"
    idx = text.lower().find("скорбалл")
    if idx != -1:
        segment = text[idx:idx + 800]
        m = re.search(r"\b([1-9][0-9]{1,2})\b", segment)
        if m:
            val = int(m.group(1))
            if 10 <= val <= 400:
                return f"балл {val}"
    head = text[:2000]
    m = re.search(r"\b([A-F][1-3])\b", head)
    if m:
        return m.group(1).upper()
    return None

def get_score_value(score_str: str) -> int:
    s = score_str.upper().strip()
    match = re.search(r"([A-F][0-9]?)", s)
    if not match:
        return 99
    s = match.group(1)
    return SCORE_ORDER.get(s, 99)

def get_score_comment(score_val: int) -> str:
    if score_val <= 2:
        return "🌟 Отличная кредитная история! Банки будут рады видеть вас."
    elif score_val <= 4:
        return "✅ Хорошая кредитная история. Многие банки готовы вас рассмотреть."
    elif score_val <= 6:
        return "👍 Удовлетворительная кредитная история. Подберём банки, готовые вас рассмотреть."
    elif score_val <= 9:
        return "💡 Средняя кредитная история. Список банков будет уже, но варианты есть."
    elif score_val <= 11:
        return "⚠️ Кредитная история ниже среднего. Банков, готовых вас рассмотреть, немного."
    elif score_val <= 12:
        return "⚠️ Слабая кредитная история. Готовы рассмотреть только отдельные банки."
    elif score_val == 13:
        return "😔 Увы, ваша кредитная история в плачевном состоянии. Банки, скорее всего, откажут."
    return ""

# ==============================
# ПАРСИНГ КРЕДИТОВ (нагрузка)
# ==============================
def parse_loans(text: str) -> dict:
    result = {
        "classic": [],
        "revolving": [],
        "guarantees": [],
        "closed": [],
        "total_load": 0.0,
    }

    blocks = re.split(r"ДОГОВОР КРЕДИТНОГО ХАРАКТЕРА №", text)
    for block in blocks[1:]:
        header = block[:300]
        is_revolving = "возобновляемой кредитной линии" in header.lower()

        # Проверка закрытия
        idx_end = header.find("Дата прекращения договора")
        is_closed = False
        if idx_end != -1:
            after = header[idx_end:idx_end + 200]
            if re.search(r"\d{2}\.\d{2}\.\d{4}", after):
                is_closed = True

        # Определяем банк по БИК
        bank_codes = {
            "ALFABY2X": "Альфа-Банк",
            "PICCBVY2X": "Приорбанк",
            "PJCBBY2X": "Приорбанк",
            "IRJSBY22": "Статусбанк",
            "POISBY2X": "Паритетбанк",
            "SLANBY22": "ВТБ (Беларусь)",
            "BELBBY2X": "Беларусбанк",
            "REDIBY2X": "РРБ-Банк",
            "BELIBY2X": "БелВЭБ",
        }
        bank_name = "Банк"
        for code, name in bank_codes.items():
            if code in block:
                bank_name = name
                break

        if is_closed:
            result["closed"].append({"bank": bank_name})
            continue

        # Ищем блок исполнения
        idx_exec = block.find("Сведения об исполнении обязательств по договору")
        if idx_exec == -1:
            continue
        exec_block = block[idx_exec:idx_exec + 2000]

        rows = re.findall(r"(\d+[.,]\d+)\s*BYN", exec_block)
        if len(rows) < 2:
            continue

        try:
            first_val = float(rows[0].replace(",", "."))

            # Находим первое значимое изменение (платёж)
            payment = 0
            for i in range(1, len(rows)):
                try:
                    val = float(rows[i].replace(",", "."))
                    diff = abs(val - first_val)
                    if diff > 50:
                        payment = round(diff, 2)
                        break
                except ValueError:
                    continue

            if is_revolving:
                payment = round(first_val * 0.05, 2)
                result["revolving"].append({"bank": bank_name, "remainder": first_val, "payment": payment})
            else:
                if payment <= 0 or payment > first_val * 0.7:
                    payment = round(first_val * 0.1, 2)
                result["classic"].append({"bank": bank_name, "payment": payment, "remainder": first_val})
        except (ValueError, IndexError):
            continue

    total = sum(item["payment"] for item in result["classic"])
    total += sum(item["payment"] for item in result["revolving"])
    result["total_load"] = round(total, 2)

    # Поручительства
    guarantee_blocks = re.split(r"ДОГОВОР ОБЕСПЕЧЕНИЯ №", text)
    for g_block in guarantee_blocks[1:]:
        amount_match = re.search(r"(\d+[.,]\d+)\s*BYN\s*\(\d{2}\.\d{2}\.\d{4}\)", g_block[:500])
        if amount_match:
            amount = float(amount_match.group(1).replace(",", "."))
            result["guarantees"].append({"bank": "Банк", "amount": amount})

    return result

# ==============================
# СТОП-ФАКТОРЫ
# ==============================
def extract_report_date(text: str):
    match = re.search(r"Дата формирования отчета[:\s]*(\d{2}\.\d{2}\.\d{4})", text, re.IGNORECASE)
    return match.group(1) if match else None

def has_current_overdue(text: str) -> bool:
    report_date_str = extract_report_date(text)
    if report_date_str:
        try:
            report_date = datetime.strptime(report_date_str, "%d.%m.%Y")
        except ValueError:
            report_date = datetime.now()
    else:
        report_date = datetime.now()
    threshold = report_date - timedelta(days=180)

    blocks = re.split(r"Сведения об исполнении обязательств по договору", text)
    for block in blocks[1:]:
        best_line = None
        best_date = None
        for line in block.split("\n"):
            line = line.strip()
            if not line:
                continue
            byn_matches = re.findall(r"(\d+[.,]\d+)\s*BYN", line)
            if len(byn_matches) < 3:
                continue
            date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", line)
            if not date_match:
                continue
            try:
                line_date = datetime.strptime(date_match.group(1), "%d.%m.%Y")
                if line_date < threshold:
                    continue
                if best_date is None or line_date > best_date:
                    best_date = line_date
                    best_line = (line, byn_matches)
            except ValueError:
                continue
        if best_line:
            _, byn_matches = best_line
            try:
                overdue_main = float(byn_matches[1].replace(",", "."))
                overdue_perc = float(byn_matches[2].replace(",", "."))
                if overdue_main > 0 or overdue_perc > 0:
                    return True
            except (ValueError, IndexError):
                continue
    return False

def has_long_overdue(text: str) -> bool:
    idx = 0
    while True:
        idx = text.find("Количество фактов просрочки", idx)
        if idx == -1:
            break
        segment = text[idx:idx + 500]
        for match in re.finditer(r"Он\.?\s*долг[\s\n:]*((?:\d+\s*){6})", segment, re.IGNORECASE):
            nums = re.findall(r"\d+", match.group(1))
            if len(nums) >= 6:
                if int(nums[4]) > 0 or int(nums[5]) > 0:
                    return True
        idx += 30
    return False

def has_executive_list(text: str) -> bool:
    patterns = [
        r"исполнительн\w*\s+лист\w*\s+по\s+кредит",
        r"исполнительн\w*\s+производств\w*\s+по\s+кредит",
        r"принудительн\w*\s+взыскание\s+по\s+кредит",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def has_mfo(text: str) -> bool:
    idx = text.find("Краткие обозначения")
    if idx != -1:
        text = text[:idx]
    idx2 = text.find("СВЕДЕНИЯ ИЗ ДОПОЛНИТЕЛЬНОЙ")
    if idx2 != -1:
        text = text[:idx2]
    idx3 = text.find("Обработка Ваших персональных данных")
    if idx3 != -1:
        text = text[:idx3]
    patterns = [
        r"ООО\s+[«\"'][^»\"']*(?:ломбард|финанс|займ|микрофинанс)",
        r"МФО\s+[«\"'][^»\"']+[«\"']",
        r"микрофинансов\w*\s+организац\w*\s+[«\"']",
        r"ломбард\w*\s+[«\"'][^»\"']+[«\"']",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def has_guarantee_overdue(text: str) -> bool:
    patterns = [
        r"просроченн\w*\s+задолженност\w*\s+по\s+поручительств",
        r"просрочк\w*\s+по\s+поручительств",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def analyze_stop_factors(text: str) -> dict:
    return {
        "current_overdue": has_current_overdue(text),
        "long_overdue": has_long_overdue(text),
        "executive_list": has_executive_list(text),
        "mfo_pawnshop": has_mfo(text),
        "guarantee_overdue": has_guarantee_overdue(text),
    }

STOP_FACTOR_MESSAGES = {
    "current_overdue": (
        "⚠️ **Обнаружена текущая просрочка** в кредитной истории. [Что делать?](https://creditregister.by)\n"
        "💡 Погасите просроченную задолженность как можно скорее."
    ),
    "long_overdue": (
        "🔴 **Просрочка более 90 дней** — автоматический отказ в большинстве банков. "
        "[Подробнее](https://minjust.gov.by/directions/enforcement/debtors/)\n"
        "💡 Погасите долг и подождите 6–12 месяцев."
    ),
    "executive_list": (
        "🔴 **Обнаружен исполнительный лист** по кредиту. "
        "[Проверить в реестре](https://minjust.gov.by/directions/enforcement/debtors/)\n"
        "💡 Закройте долг и дождитесь окончания исполнительного производства."
    ),
    "mfo_pawnshop": (
        "🟡 **Обнаружены МФО/ломбарды.** Многие банки негативно оценивают такие займы. [Что делать?](https://creditregister.by)\n"
        "💡 Закройте все микрозаймы и ломбардные займы. После этого подождите 3–6 месяцев."
    ),
    "guarantee_overdue": (
        "🔴 **Просрочка по поручительству** — серьёзный стоп-фактор.\n"
        "💡 Погасите задолженность и подождите 6+ месяцев."
    ),
}

# ==============================
# ФИНАНСОВЫЕ РАСЧЁТЫ
# ==============================
def calculate_financial_load(salary: float, payments: float, kids_count: int = 0) -> dict:
    payment_level = salary * 0.35
    kids_deduction = kids_count * 200
    free_level = payment_level - payments - kids_deduction
    return {"salary": salary, "payment_level": payment_level, "payments": payments,
            "kids_deduction": kids_deduction, "free_level": free_level}

def calculate_loan_payment(amount, annual_rate, months, payment_type):
    monthly_rate = annual_rate / 100 / 12
    if payment_type == "А":
        if monthly_rate > 0:
            payment = amount * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)
        else:
            payment = amount / months
        return {"type": "А", "monthly_payment": payment,
                "total_payment": payment * months, "overpayment": payment * months - amount}
    else:
        principal_part = amount / months
        interest_part = amount * monthly_rate
        first_payment = principal_part + interest_part
        avg_payment = principal_part + amount * monthly_rate / 2
        return {"type": "Д", "monthly_payment": first_payment, "avg_payment": avg_payment,
                "total_payment": amount + amount * monthly_rate * (months + 1) / 2,
                "overpayment": amount * monthly_rate * (months + 1) / 2}

def interpret_free_level(free: float) -> str:
    if free <= 0:
        return "⚠️ **Свободный ПУ отрицательный!** Банки, скорее всего, откажут."
    elif free < 100:
        return "⚠️ **Свободный ПУ критически низкий.** Рассмотрите меньшую сумму."
    elif free < 300:
        return "💡 **Свободный ПУ низкий.** Кредит возможен, но с осторожностью."
    else:
        return f"✅ **Отличный результат!** Останется **{free:.2f} BYN** свободных средств."

def pluralize_banks(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return "банк"
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "банка"
    return "банков"

# ==============================
# ФИЛЬТРАЦИЯ
# ==============================
def filter_banks(suitable: list, anketa: dict, loans: dict) -> list:
    filtered = list(suitable)

    if anketa.get("employment") == "self_employed":
        allowed = HIDDEN_FILTERS["self_employed"]
        filtered = [(n, i) for n, i in filtered if n in allowed]

    if anketa.get("kids", 0) > 0:
        preferred = HIDDEN_FILTERS["no_kids_deduction"]
        preferred_list = [(n, i) for n, i in filtered if n in preferred]
        other_list = [(n, i) for n, i in filtered if n not in preferred]
        filtered = preferred_list + other_list

    if anketa.get("exec_list") == "open":
        filtered = []
    elif anketa.get("exec_list") == "closed_less":
        allowed = HIDDEN_FILTERS["loyal_to_exec"]
        filtered = [(n, i) for n, i in filtered if n in allowed]

    if anketa.get("pawnshop") == "open":
        allowed = HIDDEN_FILTERS["loyal_to_mfo"]
        filtered = [(n, i) for n, i in filtered if n in allowed]

    return filtered

# ==============================
# КЛАВИАТУРЫ
# ==============================
def get_start_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Старт")],
                  [KeyboardButton(text="💰 Что такое рефинансирование?")],
                  [KeyboardButton(text="📄 Где взять кредитную историю")],
                  [KeyboardButton(text="🏦 Лучшие предложения банков")],
                  [KeyboardButton(text="🔄 Перезагрузка")]],
        resize_keyboard=True, input_field_placeholder="Нажмите Старт для начала")

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📥 Загрузить PDF")],
                  [KeyboardButton(text="💰 Что такое рефинансирование?")],
                  [KeyboardButton(text="📄 Где взять кредитную историю")],
                  [KeyboardButton(text="🏦 Лучшие предложения банков")],
                  [KeyboardButton(text="🔄 Перезагрузка")]],
        resize_keyboard=True, input_field_placeholder="Загрузите PDF или документ...")

def get_yes_no_kb(prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data=f"{prefix}_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data=f"{prefix}_no")]])

def get_job_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Официально", callback_data="job_official")],
        [InlineKeyboardButton(text="❌ Не официально", callback_data="job_unofficial")],
        [InlineKeyboardButton(text="💼 Самозанятый", callback_data="job_self")],
        [InlineKeyboardButton(text="🎖 Военнослужащий", callback_data="job_military")],
        [InlineKeyboardButton(text="⏭️ Пропустить анкету", callback_data="skip_anketa")]])

def get_kids_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Детей пока нет", callback_data="kids_0")],
        [InlineKeyboardButton(text="1 ребёнок", callback_data="kids_1")],
        [InlineKeyboardButton(text="2 ребёнка", callback_data="kids_2")],
        [InlineKeyboardButton(text="3 и более", callback_data="kids_3")]])

def get_family_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Женат / Замужем", callback_data="family_married")],
        [InlineKeyboardButton(text="Разведён(а)", callback_data="family_divorced")],
        [InlineKeyboardButton(text="Холост / Не замужем", callback_data="family_single")],
        [InlineKeyboardButton(text="Вдова / Вдовец", callback_data="family_widow")]])

def get_exec_list_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нет, не было", callback_data="exec_no")],
        [InlineKeyboardButton(text="Были, закрыты < 1.5 лет", callback_data="exec_closed_less")],
        [InlineKeyboardButton(text="Были, закрыты > 1.5 лет", callback_data="exec_closed_more")],
        [InlineKeyboardButton(text="Есть открытые", callback_data="exec_open")]])

def get_pawnshop_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нет", callback_data="pawn_no")],
        [InlineKeyboardButton(text="Есть открытые", callback_data="pawn_open")],
        [InlineKeyboardButton(text="Есть закрытые", callback_data="pawn_closed")]])

def get_choice_keyboard(has_stop=False):
    rows = [
        [InlineKeyboardButton(text="📋 Показать список банков", callback_data="show_banks")],
        [InlineKeyboardButton(text="📄 Уточнить данные", callback_data="clarify_income")],
        [InlineKeyboardButton(text="💰 Рефинансирование", callback_data="refinance_info")]]
    if has_stop:
        rows.append([InlineKeyboardButton(text="💡 Как улучшить КИ", callback_data="improve_ci")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_income_cert_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, могу взять справку", callback_data="income_yes")],
        [InlineKeyboardButton(text="❌ Нет, не могу", callback_data="income_no")]])

def get_income_cert_keyboard_after():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, могу взять справку", callback_data="show_cert_yes")],
        [InlineKeyboardButton(text="❌ Нет, не могу", callback_data="show_cert_no")]])

def get_upload_pdf_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Где взять PDF?", callback_data="how_to_get_pdf")]])

def get_loan_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Аннуитет — равными платежами", callback_data="loan_type_A")],
        [InlineKeyboardButton(text="📉 Дифференцированный — уменьшается", callback_data="loan_type_D")]])

async def ask_pdf(message: types.Message):
    await message.answer(
        "📥 **Загрузите PDF-документ.**\n\n"
        "Просто отправьте файл в этот чат — я сразу начну анализ.\n\n"
        "⚠️ Файл будет обработан и удалён после анализа.",
        parse_mode="Markdown",
        reply_markup=get_upload_pdf_keyboard())
    await message.answer(
        "После получения файла — отправьте его в чат 👇",
        reply_markup=ReplyKeyboardRemove())

# ==============================
# КОМАНДА /start
# ==============================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать в Финансовый Аналитик!**\n\n"
        "Я проведу анкету, проанализирую вашу кредитную историю "
        "и подберу банки Беларуси.\n\n"
        "⚠️ Сервис носит исключительно информационный характер.\n\n"
        "👇 Нажмите «🚀 Старт».",
        reply_markup=get_start_menu(), parse_mode="Markdown")

@dp.message(F.text == "🚀 Старт")
async def btn_start(message: types.Message):
    uid = message.from_user.id
    user_calc[uid] = {"anketa_passed": False}
    user_states[uid] = "anketa_job"
    await message.answer(
        "📋 **Анкета (1/10).**\n\n**Ваш тип занятости?**\n\n"
        "Выберите подходящий вариант 👇",
        parse_mode="Markdown", reply_markup=get_job_kb())

@dp.callback_query(F.data == "skip_anketa")
async def skip_anketa(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user_calc[uid]["anketa_passed"] = False
    user_states[uid] = None
    await callback.message.edit_text("⏭️ **Анкета пропущена.**", parse_mode="Markdown")
    await ask_pdf(callback.message)
    await callback.answer()

@dp.callback_query(F.data.in_({"job_official", "job_unofficial", "job_self", "job_military"}))
async def anketa_job(callback: types.CallbackQuery):
    uid = callback.from_user.id
    labels = {
        "job_official": ("official", "Официально"),
        "job_unofficial": ("unofficial", "Не официально"),
        "job_self": ("self_employed", "Самозанятый"),
        "job_military": ("military", "Военнослужащий"),
    }
    value, label = labels[callback.data]
    user_calc[uid]["employment"] = value
    user_states[uid] = "anketa_income"
    await callback.message.edit_text(
        f"✅ Тип занятости: **{label}**\n\n"
        "📋 **Анкета (2/10).**\n\nУкажите ваш **среднемесячный доход** (числом в BYN).\n\n"
        "Например: `1500`", parse_mode="Markdown")
    await callback.answer()

# ==============================
# ТЕКСТОВЫЕ ОТВЕТЫ
# ==============================
@dp.message(F.text, ~F.text.in_({"🚀 Старт", "📥 Загрузить PDF", "💰 Что такое рефинансирование?",
                                   "📄 Где взять кредитную историю", "🏦 Лучшие предложения банков",
                                   "🔄 Перезагрузка"}))
async def handle_text_input(message: types.Message):
    uid = message.from_user.id
    state = user_states.get(uid)

    def parse_number(text):
        try:
            return float(text.replace(",", ".").replace(" ", "").replace("by", "").replace("BY", "").strip())
        except ValueError:
            return None

    if state == "anketa_income":
        salary = parse_number(message.text)
        if salary is None or salary <= 0:
            await message.answer("⚠️ Введите корректное число (например, 1500).")
            return
        user_calc[uid]["salary"] = salary
        user_states[uid] = "anketa_tenure"
        await message.answer(
            f"✅ Доход: **{salary:.0f} BYN**\n\n"
            "📋 **Анкета (3/10).**\n\n**Вы работаете на последнем месте больше 3 месяцев?**",
            parse_mode="Markdown", reply_markup=get_yes_no_kb("tenure"))
        return

    if state == "anketa_amount":
        amount = parse_number(message.text)
        if amount is None or amount <= 0:
            await message.answer("⚠️ Введите корректную сумму (например, 20000).")
            return
        user_calc[uid]["loan_amount"] = amount
        user_calc[uid]["anketa_passed"] = True
        user_states[uid] = None
        await message.answer(
            f"✅ Желаемая сумма: **{amount:.0f} BYN**\n\n"
            "📋 **Анкета завершена!**", parse_mode="Markdown")
        await ask_pdf(message)
        return

    if state == "waiting_loan_amount":
        amount = parse_number(message.text)
        if amount is None or amount <= 0:
            await message.answer("⚠️ Введите корректную сумму.")
            return
        user_calc[uid]["loan_amount"] = amount
        user_states[uid] = None
        await message.answer(f"✅ Сумма: **{amount:.0f} BYN**\n\nВыберите тип платежа:",
                             parse_mode="Markdown", reply_markup=get_loan_type_keyboard())
        return

    if state == "waiting_loan_amount_for_bank":
        amount = parse_number(message.text)
        if amount is None or amount <= 0:
            await message.answer("⚠️ Введите корректную сумму.")
            return
        bank_name = user_calc.get(uid, {}).get("selected_bank")
        if not bank_name or bank_name not in BANKS_DATA:
            await message.answer("⚠️ Банк не выбран.")
            user_states[uid] = None
            return
        info = BANKS_DATA[bank_name]
        result = calculate_loan_payment(amount, info['rate'], info['term_months'], info['payment_type'])
        free_level = user_calc.get(uid, {}).get("free_level")
        type_label = "Аннуитет — равными платежами" if info['payment_type'] == "А" else "Дифференцированный — уменьшается"
        report = f"💳 **Кредит в «{bank_name}»**\n\n"
        report += f"💰 Сумма: **{amount:.0f} BYN**\n"
        report += f"📉 Ставка: **{info['rate']}%** | 📅 {info['term']}\n"
        report += f"📊 Тип: **{type_label}**\n\n"
        if info['payment_type'] == "А":
            report += f"💵 Платёж: **{result['monthly_payment']:.2f} BYN**\n"
        else:
            report += f"💵 Первый: **{result['monthly_payment']:.2f} BYN**\n"
            report += f"📊 Средний: **{result['avg_payment']:.2f} BYN**\n"
        report += f"💸 Переплата: **{result['overpayment']:.2f} BYN**\n"
        if free_level is not None:
            effective = result['monthly_payment'] if info['payment_type'] == "А" else result['avg_payment']
            new_free_level = free_level - effective
            report += f"━━━━━━━━━━━━━━━━\nПУ после: **{new_free_level:.2f} BYN**\n\n"
            report += interpret_free_level(new_free_level)

        score_val = pdf_cache.get(uid, {}).get("score_val")
        amount_req = user_calc.get(uid, {}).get("loan_amount", 0)
        if score_val and score_val <= 5 and amount_req < 30000:
            report += "\n💡 _Если нужна помощь с оформлением — свяжитесь с менеджером._"
        else:
            report += "\n📞 _Рекомендуем связаться с менеджером — базового анализа может быть недостаточно._"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🏦 Сайт {bank_name}", url=info['url'])],
            [InlineKeyboardButton(text="📞 Связаться с менеджером", url=f"https://t.me/{MANAGER_TG.lstrip('@')}")]])
        await message.answer(report, parse_mode="Markdown", reply_markup=kb)
        user_states[uid] = None
        return

    await message.answer("📥 Загрузите PDF-документ или выберите пункт меню 👇",
                         reply_markup=get_main_menu())

# ==============================
# АНКЕТА — callback
# ==============================
@dp.callback_query(F.data.in_({"tenure_yes", "tenure_no"}))
async def anketa_tenure(callback: types.CallbackQuery):
    uid = callback.from_user.id
    value = callback.data == "tenure_yes"
    user_calc[uid]["tenure_3m"] = value
    user_states[uid] = "anketa_kids"
    label = "более 3 месяцев" if value else "менее 3 месяцев"
    await callback.message.edit_text(
        f"✅ Срок на последнем месте: **{label}**\n\n"
        "📋 **Анкета (4/10).**\n\n**Сколько у вас детей до 18 лет?**",
        parse_mode="Markdown", reply_markup=get_kids_kb())
    await callback.answer()

@dp.callback_query(F.data.startswith("kids_"))
async def anketa_kids(callback: types.CallbackQuery):
    uid = callback.from_user.id
    kids_map = {"kids_0": 0, "kids_1": 1, "kids_2": 2, "kids_3": 3}
    kids = kids_map.get(callback.data, 0)
    user_calc[uid]["kids"] = kids
    user_states[uid] = "anketa_family"
    kids_str = "Детей пока нет" if kids == 0 else f"{kids}"
    await callback.message.edit_text(
        f"✅ Дети: **{kids_str}**\n\n"
        "📋 **Анкета (5/10).**\n\n**Ваш семейный статус?**",
        parse_mode="Markdown", reply_markup=get_family_kb())
    await callback.answer()

@dp.callback_query(F.data.in_({"family_married", "family_divorced", "family_single", "family_widow"}))
async def anketa_family(callback: types.CallbackQuery):
    uid = callback.from_user.id
    labels = {
        "family_married": "Женат / Замужем",
        "family_divorced": "Разведён(а)",
        "family_single": "Холост / Не замужем",
        "family_widow": "Вдова / Вдовец",
    }
    user_calc[uid]["family"] = callback.data.replace("family_", "")
    user_states[uid] = "anketa_cert"
    await callback.message.edit_text(
        f"✅ Семейный статус: **{labels[callback.data]}**\n\n"
        "📋 **Анкета (6/10).**\n\n**Есть ли у вас возможность взять справку о доходах?**",
        parse_mode="Markdown", reply_markup=get_income_cert_keyboard())
    await callback.answer()

@dp.callback_query(F.data.in_({"income_yes", "income_no"}))
async def anketa_cert(callback: types.CallbackQuery):
    uid = callback.from_user.id
    has_cert = callback.data == "income_yes"
    user_calc[uid]["has_cert"] = has_cert
    user_states[uid] = "anketa_special"
    label = "Да" if has_cert else "Нет"
    await callback.message.edit_text(
        f"✅ Возможность справки: **{label}**\n\n"
        "📋 **Анкета (7/10).**\n\n**Вы сотрудник МВД, МЧС, военнослужащий или другой силовой структуры?**",
        parse_mode="Markdown", reply_markup=get_yes_no_kb("special"))
    await callback.answer()

@dp.callback_query(F.data.in_({"special_yes", "special_no"}))
async def anketa_special(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user_calc[uid]["special"] = callback.data == "special_yes"
    user_states[uid] = "anketa_exec"
    await callback.message.edit_text(
        "✅ Спецкатегория: **" + ("Да" if callback.data == "special_yes" else "Нет") + "**\n\n"
        "📋 **Анкета (8/10).**\n\n**Были ли у вас исполнительные листы?**",
        parse_mode="Markdown", reply_markup=get_exec_list_kb())
    await callback.answer()

@dp.callback_query(F.data.in_({"exec_no", "exec_closed_less", "exec_closed_more", "exec_open"}))
async def anketa_exec(callback: types.CallbackQuery):
    uid = callback.from_user.id
    labels = {
        "exec_no": "Нет, не было",
        "exec_closed_less": "Были, закрыты < 1.5 лет",
        "exec_closed_more": "Были, закрыты > 1.5 лет",
        "exec_open": "Есть открытые",
    }
    user_calc[uid]["exec_list"] = callback.data.replace("exec_", "")
    user_states[uid] = "anketa_pawn"
    await callback.message.edit_text(
        f"✅ Исполнительные листы: **{labels[callback.data]}**\n\n"
        "📋 **Анкета (9/10).**\n\n**Есть ли у вас открытые ломбарды?**",
        parse_mode="Markdown", reply_markup=get_pawnshop_kb())
    await callback.answer()

@dp.callback_query(F.data.in_({"pawn_no", "pawn_open", "pawn_closed"}))
async def anketa_pawn(callback: types.CallbackQuery):
    uid = callback.from_user.id
    labels = {"pawn_no": "Нет", "pawn_open": "Есть открытые", "pawn_closed": "Есть закрытые"}
    user_calc[uid]["pawnshop"] = callback.data.replace("pawn_", "")
    user_states[uid] = "anketa_amount"
    await callback.message.edit_text(
        f"✅ Ломбарды: **{labels[callback.data]}**\n\n"
        "📋 **Анкета (10/10).**\n\nУкажите **желаемую сумму кредита** (числом в BYN).\n\n"
        "Например: `20000`", parse_mode="Markdown")
    await callback.answer()

# ==============================
# ОБРАБОТКА PDF
# ==============================
@dp.message(F.document)
async def handle_document(message: types.Message):
    uid = message.from_user.id
    doc = message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await message.answer("⚠️ Отправьте файл в формате PDF.")
        return
    if doc.file_size > 10 * 1024 * 1024:
        await message.answer("⚠️ Файл больше 10 МБ.")
        return

    await message.answer("⏳ **Идёт анализ...** Подождите 10–15 секунд.",
                         reply_markup=ReplyKeyboardRemove())

    file = await bot.get_file(doc.file_id)
    file_path = f"downloads/{doc.file_name}"
    await bot.download_file(file.file_path, file_path)
    try:
        text = extract_text_from_pdf(file_path)
    except Exception as e:
        await message.answer(f"❌ Ошибка чтения PDF: {e}")
        if os.path.exists(file_path): os.remove(file_path)
        return

    user_score_str = extract_user_score(text)
    user_score_val = None
    stop_factors = analyze_stop_factors(text)
    loans = parse_loans(text)

    report = "📊 **Ваш отчёт:**\n\n"

    if user_score_str:
        if "балл" in user_score_str:
            report += f"📈 Скор-балл: **{user_score_str}**\n"
        else:
            user_score_val = get_score_value(user_score_str)
            report += f"📈 Кредитный рейтинг: **{user_score_str}**\n"
            comment = get_score_comment(user_score_val)
            if comment:
                report += f"{comment}\n"
    else:
        report += "⚠️ Не удалось определить рейтинг.\n"

    if loans["total_load"] > 0:
        report += f"\n💰 **Текущая нагрузка:** ≈ {loans['total_load']:.0f} BYN/мес\n"
        if loans["classic"]:
            report += "• Классические кредиты:\n"
            for item in loans["classic"]:
                report += f"   — {item['bank']}: ≈ {item['payment']:.0f} BYN\n"
        if loans["revolving"]:
            report += "• Возобновляемые линии:\n"
            for item in loans["revolving"]:
                report += f"   — {item['bank']}: ≈ {item['payment']:.0f} BYN\n"

    anketa = user_calc.get(uid, {})
    if anketa.get("employment") == "unofficial":
        report += "⚠️ Без официального трудоустройства большинство банков откажут.\n"
    if anketa.get("tenure_3m") is False:
        report += "⚠️ Срок на последнем месте < 3 месяцев — минус для банка.\n"
    if anketa.get("special"):
        report += "ℹ️ Спецкатегория (МВД/МЧС/военный): возможна скрытая КИ и ФСЗН.\n"

    found_stops = [k for k, v in stop_factors.items() if v]
    if found_stops:
        report += "\n🚨 **Обнаружены стоп-факторы:**\n\n"
        for key in found_stops:
            report += STOP_FACTOR_MESSAGES.get(key, "") + "\n\n"
    else:
        report += "✅ Явных стоп-факторов не найдено.\n\n"

    suitable = []
    if user_score_val and user_score_str.strip().upper() != "F":
        for bank_name, info in BANKS_DATA.items():
            if user_score_val <= get_score_value(info['min_score']):
                suitable.append((bank_name, info))
        suitable.sort(key=lambda x: x[1]['rate'])

    suitable = filter_banks(suitable, anketa, loans)

    pdf_cache[uid] = {
        "score_val": user_score_val,
        "score_str": user_score_str,
        "stop_factors": stop_factors,
        "suitable": suitable,
        "found_stops": found_stops,
        "loans": loans,
    }

    if not user_score_val:
        await message.answer(report + "💡 Для подбора банков нужен рейтинг.",
                             parse_mode="Markdown", reply_markup=get_main_menu())
    elif user_score_str.strip().upper() == "F":
        await message.answer(
            report + "😔 **Рейтинг F — заявки не рассматриваются.**\n\n"
            "💡 Погасите просрочки, закройте МФО и ломбарды, подождите 6–12 месяцев.",
            parse_mode="Markdown", reply_markup=get_main_menu())
    elif not suitable:
        await message.answer(report + "😔 **Нет подходящих банков.**",
                             parse_mode="Markdown", reply_markup=get_main_menu())
    else:
        cnt = min(len(suitable), 3)
        word = pluralize_banks(cnt)
        anketa_passed = anketa.get("anketa_passed", False)

        if anketa_passed:
            has_cert = anketa.get("has_cert", False)
            shown = suitable[:3]
            short_report = f"🏦 **{cnt} {word} с лучшими условиями:**\n\n"
            for i, (bank_name, info) in enumerate(shown, 1):
                type_label = "А" if info['payment_type'] == "А" else "Д"
                sum_shown = info['sum_with_cert'] if has_cert else info['sum_without_cert']
                short_report += f"{i}. [{bank_name}]({info['url']}) — {info['rate']}% ({type_label}), {sum_shown}\n"
            short_report += "\n_А — аннуитет, Д — дифференцированный_"
            short_report += f"\n{'✅ Со справкой о доходах' if has_cert else '❌ Без справки о доходах'}"

            bank_buttons = []
            for bank_name, info in shown:
                idx = BANK_KEYS.index(bank_name)
                bank_buttons.append([InlineKeyboardButton(
                    text=f"💳 {bank_name}", callback_data=f"bank_calc_{idx}")])
            extra = []
            if found_stops:
                extra.append([InlineKeyboardButton(
                    text="💡 Как улучшить кредитную историю", callback_data="improve_ci")])

            if user_score_val and user_score_val <= 5 and (anketa.get("loan_amount") or 0) < 30000:
                cta = "\n\n💡 _Если нужна помощь с оформлением — свяжитесь с менеджером._"
            else:
                cta = "\n\n📞 _Рекомендуем связаться с менеджером — базового анализа может быть недостаточно._"

            await message.answer(report, parse_mode="Markdown")
            await message.answer(
                short_report + cta, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=bank_buttons + extra + [
                    [InlineKeyboardButton(text="📞 Связаться с менеджером", url=f"https://t.me/{MANAGER_TG.lstrip('@')}")]]))
        else:
            await message.answer(
                report + f"🏦 **Подобрано {cnt} {word} с лучшими условиями для вас.**\n\n"
                "Чтобы подобрать точнее, уточните данные 👇",
                parse_mode="Markdown",
                reply_markup=get_choice_keyboard(has_stop=bool(found_stops)))

    try: os.remove(file_path)
    except: pass

# ==============================
# СПИСОК БАНКОВ / УТОЧНЕНИЕ
# ==============================
@dp.callback_query(F.data == "show_banks")
async def show_banks(callback: types.CallbackQuery):
    uid = callback.from_user.id
    cache = pdf_cache.get(uid)
    if not cache:
        await callback.answer("Данные устарели.", show_alert=True)
        return
    suitable = cache["suitable"]
    shown = suitable[:3]
    cnt = len(shown)
    word = pluralize_banks(cnt)
    report = f"🏦 **{cnt} {word} с лучшими условиями:**\n\n"
    for i, (bank_name, info) in enumerate(shown, 1):
        type_label = "А" if info['payment_type'] == "А" else "Д"
        report += f"{i}. [{bank_name}]({info['url']}) — {info['rate']}% ({type_label}), {info['sum_without_cert']}\n"
    report += "\n_А — аннуитет, Д — дифференцированный_"
    bank_buttons = []
    for bank_name, info in shown:
        idx = BANK_KEYS.index(bank_name)
        bank_buttons.append([InlineKeyboardButton(text=f"💳 {bank_name}", callback_data=f"bank_calc_{idx}")])
    extra = [[InlineKeyboardButton(text="📄 Уточнить данные", callback_data="clarify_income")],
             [InlineKeyboardButton(text="💰 Рефинансирование", callback_data="refinance_info")],
             [InlineKeyboardButton(text="📞 Связаться с менеджером", url=f"https://t.me/{MANAGER_TG.lstrip('@')}")]]
    if cache.get("found_stops"):
        extra.append([InlineKeyboardButton(text="💡 Как улучшить КИ", callback_data="improve_ci")])
    await callback.message.edit_text(report, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=bank_buttons + extra))
    await callback.answer()

@dp.callback_query(F.data == "clarify_income")
async def clarify_income(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📄 **Есть ли у вас возможность взять справку о доходах?**\n\n"
        "От этого зависит максимальная сумма кредита в каждом банке.",
        parse_mode="Markdown", reply_markup=get_income_cert_keyboard_after())
    await callback.answer()

@dp.callback_query(F.data.in_({"show_cert_yes", "show_cert_no"}))
async def handle_income_cert_after(callback: types.CallbackQuery):
    uid = callback.from_user.id
    has_cert = callback.data == "show_cert_yes"
    cache = pdf_cache.get(uid)
    if not cache:
        await callback.answer("Данные устарели.", show_alert=True)
        return
    user_calc.setdefault(uid, {})["has_cert"] = has_cert
    suitable = cache["suitable"]
    if not suitable:
        await callback.message.edit_text("😔 Нет подходящих банков.")
        await callback.answer()
        return
    shown = suitable[:3]
    cnt = len(shown)
    word = pluralize_banks(cnt)
    report = f"🏦 **{cnt} {word} с лучшими условиями:**\n\n"
    for i, (bank_name, info) in enumerate(shown, 1):
        type_label = "А" if info['payment_type'] == "А" else "Д"
        sum_shown = info['sum_with_cert'] if has_cert else info['sum_without_cert']
        report += f"{i}. [{bank_name}]({info['url']}) — {info['rate']}% ({type_label}), {sum_shown}\n"
    report += "\n_А — аннуитет, Д — дифференцированный_"
    report += f"\n{'✅ Со справкой о доходах' if has_cert else '❌ Без справки о доходах'}"
    bank_buttons = []
    for bank_name, info in shown:
        idx = BANK_KEYS.index(bank_name)
        bank_buttons.append([InlineKeyboardButton(
            text=f"💳 {bank_name}", callback_data=f"bank_calc_{idx}")])
    extra = [[InlineKeyboardButton(text="📄 Уточнить данные", callback_data="clarify_income")],
             [InlineKeyboardButton(text="💰 Рефинансирование", callback_data="refinance_info")],
             [InlineKeyboardButton(text="📞 Связаться с менеджером", url=f"https://t.me/{MANAGER_TG.lstrip('@')}")]]
    if cache.get("found_stops"):
        extra.append([InlineKeyboardButton(
            text="💡 Как улучшить КИ", callback_data="improve_ci")])
    await callback.message.edit_text(
        report, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=bank_buttons + extra))
    await callback.answer()

# ==============================
# ИНСТРУКЦИИ
# ==============================
@dp.callback_query(F.data == "how_to_get_pdf")
async def show_how_to_get_pdf(callback: types.CallbackQuery):
    await callback.message.answer(
        "📄 **Как получить кредитную историю в Беларуси:**\n\n"
        "**1. Онлайн (самый простой способ):**\n"
        "🔗 https://creditregister.by\n"
        "• Пройдите идентификацию через МСИ\n"
        "• Нажмите «Получить кредитный отчёт»\n"
        "• Скачайте PDF-файл\n\n"
        "**2. Лично в Нацбанке:**\n"
        "📍 г. Минск, ул. Толстого, 6\n"
        "📞 (017) 218-38-88, 218-38-93\n\n"
        "**3. По почте:**\n"
        "Отправьте нотариально заверенное заявление\n\n"
        "💰 **Стоимость:** первые **2 отчёта в год — бесплатно**.",
        parse_mode="Markdown",
        reply_markup=get_main_menu(),
        disable_web_page_preview=True)
    await callback.answer()

@dp.message(F.text == "💰 Что такое рефинансирование?")
async def btn_refinance_info(message: types.Message):
    await message.answer(
        "💰 **Что такое рефинансирование?**\n\n"
        "Это когда вы **объединяете несколько кредитов в один** — "
        "берёте новый кредит, чтобы погасить старые.\n\n"
        "**Зачем это нужно:**\n"
        "• ✅ Один платёж вместо 3–5 — удобнее\n"
        "• ✅ Обычно меньше ежемесячный платёж\n"
        "• ✅ Можно выбрать банк с лучшей ставкой\n"
        "• ✅ Освобождается часть платёжного уровня — "
        "появляется пространство для нового кредита\n\n"
        "**Пример:**\n"
        "У вас 3 кредита: 400 + 300 + 250 = 950 BYN/мес.\n"
        "После рефинансирования: 1 кредит на 8 000 BYN "
        "под 18% на 5 лет → платёж ~205 BYN/мес.\n\n"
        "**Экономия: 745 BYN/мес** 💰\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 Хотите узнать, подходит ли вам рефинансирование? "
        "Загрузите PDF с кредитной историей — я посчитаю.\n\n"
        "📞 Для детального разбора — свяжитесь с менеджером.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Связаться с менеджером", url=f"https://t.me/{MANAGER_TG.lstrip('@')}")]]))

@dp.callback_query(F.data == "refinance_info")
async def show_refinance_info(callback: types.CallbackQuery):
    await callback.message.answer(
        "💰 **Рефинансирование** — это объединение нескольких кредитов в один.\n\n"
        "**Что даёт:**\n"
        "• Один платёж вместо нескольких\n"
        "• Меньше нагрузка на бюджет\n"
        "• Можно взять больше денег\n\n"
        "📞 Для точного расчёта — свяжитесь с менеджером.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Связаться с менеджером", url=f"https://t.me/{MANAGER_TG.lstrip('@')}")]]))
    await callback.answer()

@dp.callback_query(F.data == "improve_ci")
async def show_improve_ci(callback: types.CallbackQuery):
    await callback.message.answer(
        "💡 **Как улучшить кредитную историю:**\n\n"
        "**1. Погасите все просрочки.** [Проверить КИ](https://creditregister.by)\n\n"
        "**2. Закройте микрозаймы и ломбарды.** Даже без просрочек — это стоп-фактор.\n\n"
        "**3. Закройте исполнительные производства.** [Проверить долги](https://minjust.gov.by/directions/enforcement/debtors/)\n\n"
        "**4. Не подавайте много заявок.** 5+ запросов за месяц — банк насторожится.\n\n"
        "**5. Платите вовремя** по действующим кредитам.\n\n"
        "**6. Подождите 6–12 месяцев.** КИ обновляется.\n\n"
        "**7. Возьмите небольшую рассрочку** и гасите её — это создаёт положительную историю.\n\n"
        "⚠️ Рейтинг F не исправить за один день. Реальный срок — **6–24 месяца**.",
        parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

# ==============================
# РАСЧЁТ ПОД БАНК
# ==============================
@dp.callback_query(F.data.startswith("bank_calc_"))
async def bank_calc_start(callback: types.CallbackQuery):
    uid = callback.from_user.id
    try:
        idx = int(callback.data.replace("bank_calc_", ""))
        bank_name = BANK_KEYS[idx]
    except (ValueError, IndexError):
        await callback.answer("Банк не найден", show_alert=True)
        return
    user_calc.setdefault(uid, {})["selected_bank"] = bank_name
    info = BANKS_DATA[bank_name]
    type_label = "аннуитет (равными платежами)" if info['payment_type'] == "А" else "дифференцированный (уменьшается)"

    amount = user_calc.get(uid, {}).get("loan_amount")
    if amount:
        result = calculate_loan_payment(amount, info['rate'], info['term_months'], info['payment_type'])
        free_level = user_calc.get(uid, {}).get("free_level")
        report = f"💳 **Кредит в «{bank_name}»**\n\n"
        report += f"💰 Сумма: **{amount:.0f} BYN**\n"
        report += f"📉 Ставка: **{info['rate']}%** | 📅 {info['term']}\n"
        report += f"📊 Тип: **{type_label}**\n\n"
        if info['payment_type'] == "А":
            report += f"💵 Платёж: **{result['monthly_payment']:.2f} BYN**\n"
        else:
            report += f"💵 Первый: **{result['monthly_payment']:.2f} BYN**\n"
            report += f"📊 Средний: **{result['avg_payment']:.2f} BYN**\n"
        report += f"💸 Переплата: **{result['overpayment']:.2f} BYN**\n"
        if free_level is not None:
            effective = result['monthly_payment'] if info['payment_type'] == "А" else result['avg_payment']
            new_free_level = free_level - effective
            report += f"━━━━━━━━━━━━━━━━\nПУ после: **{new_free_level:.2f} BYN**\n\n"
            report += interpret_free_level(new_free_level)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🏦 Сайт {bank_name}", url=info['url'])],
            [InlineKeyboardButton(text="📞 Связаться с менеджером", url=f"https://t.me/{MANAGER_TG.lstrip('@')}")]])
        await callback.message.answer(report, parse_mode="Markdown", reply_markup=kb)
        await callback.answer()
        return

    user_states[uid] = "waiting_loan_amount_for_bank"
    await callback.message.answer(
        f"💳 **Кредит в «{bank_name}»**\n\n"
        f"📉 Ставка: **{info['rate']}%** | 📅 {info['term']}\n"
        f"📊 Тип: **{type_label}**\n\n"
        "Укажите **желаемую сумму** (числом в BYN).\n\nНапример: `20000`",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

# ==============================
# МЕНЮ
# ==============================
@dp.message(F.text == "📄 Где взять кредитную историю")
async def btn_where(message: types.Message):
    await message.answer(
        "📄 **Как получить кредитную историю:**\n\n"
        "**1. Онлайн:**\n🔗 https://creditregister.by\n"
        "• Идентификация через МСИ\n• «Получить кредитный отчёт»\n\n"
        "**2. Лично:** г. Минск, ул. Толстого, 6\n📞 (017) 218-38-88\n\n"
        "**3. По почте:** нотариально заверенное заявление\n\n"
        "💰 Первые **2 отчёта в год — бесплатно**.",
        reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.message(F.text == "🏦 Лучшие предложения банков")
async def btn_best(message: types.Message):
    text = "🏦 **Топ-5 банков по ставкам:**\n\n"
    for name, info in list(BANKS_DATA.items())[:5]:
        type_label = "А" if info['payment_type'] == "А" else "Д"
        text += f"[{name}]({info['url']}) — {info['rate']}% ({type_label})\n"
    text += "\n_А — аннуитет, Д — дифференцированный_"
    text += "\n_Полный подбор — после загрузки PDF._"
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.message(F.text == "🔄 Перезагрузка")
async def btn_restart(message: types.Message):
    uid = message.from_user.id
    user_states[uid] = None
    user_calc.pop(uid, None)
    pdf_cache.pop(uid, None)
    try:
        for f in os.listdir("downloads"):
            fp = os.path.join("downloads", f)
            if os.path.isfile(fp): os.remove(fp)
        info = "🗑️ Временные файлы удалены."
    except Exception as e:
        info = f"⚠️ Ошибка: {e}"
    await message.answer(f"🔄 **Перезагружено.**\n\n{info}\n\nНажмите «🚀 Старт».",
                         reply_markup=get_start_menu(), parse_mode="Markdown")

@dp.message(F.text == "📥 Загрузить PDF")
async def btn_upload(message: types.Message):
    await ask_pdf(message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())