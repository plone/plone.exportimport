from datetime import datetime
from DateTime import DateTime
from dateutil import parser


def parse_datetime(value: str) -> datetime | None:
    """Parse a value and return a datetime instance."""
    if value:
        try:
            result = parser.parse(value)
        except parser.ParserError:
            result = None
        return result


def parse_date(value: str) -> DateTime | None:
    """Parse a value and return a DateTime instance."""
    if value:
        parsed = parse_datetime(value)
        return DateTime(parsed) if parsed else None
