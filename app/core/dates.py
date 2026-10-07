import calendar
from datetime import date


def first_of_month(value: date) -> date:
    return value.replace(day=1)


def add_months(value: date, months: int) -> date:
    year, month = divmod(value.year * 12 + value.month - 1 + months, 12)
    return date(year, month + 1, 1)


def month_bounds(value: date) -> tuple[date, date]:
    start = first_of_month(value)
    return start, start.replace(day=calendar.monthrange(start.year, start.month)[1])


def parse_month(text: str) -> date:
    year, month = text.split("-")
    return date(int(year), int(month), 1)
