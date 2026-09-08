import re

# A cell whose first non-whitespace character is one of these is treated as a
# formula by Excel / LibreOffice Calc / Google Sheets. A leading tab or carriage
# return can also let a payload jump into an adjacent cell.
_FORMULA_TRIGGERS = ("=", "+", "-", "@")

# Fully numeric strings (including negatives, decimals and scientific notation)
# are safe and must pass through untouched, otherwise a real score of "-1" or
# "-3.5" would be mangled into "'-1".
_NUMERIC_RE = re.compile(r"^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")


def csv_safe_cell(value):
    """Neutralize spreadsheet formula / DDE injection in an exported CSV cell.

    Values that would be interpreted as a formula are prefixed with a single
    apostrophe so the spreadsheet renders them as literal text. Numbers (both
    numeric types and numeric strings) and plain text are returned unchanged.
    Embedded newlines are left alone: csv.writer already quotes them, so they
    cannot break the row structure.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return value

    text = str(value)
    stripped = text.lstrip()
    if not stripped or _NUMERIC_RE.match(stripped):
        return text
    if stripped[0] in _FORMULA_TRIGGERS or text[:1] in ("\t", "\r"):
        return "'" + text
    return text
