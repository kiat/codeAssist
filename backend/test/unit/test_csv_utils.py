from util.csv_utils import csv_safe_cell


def test_passes_through_plain_text():
    assert csv_safe_cell("Alice Example") == "Alice Example"
    assert csv_safe_cell("passed") == "passed"
    assert csv_safe_cell("8 / 4 * 2") == "8 / 4 * 2"


def test_none_becomes_empty_string():
    assert csv_safe_cell(None) == ""


def test_numeric_types_pass_through_unchanged():
    assert csv_safe_cell(0) == 0
    assert csv_safe_cell(-1) == -1
    assert csv_safe_cell(2.5) == 2.5
    assert csv_safe_cell(True) == "True"


def test_numeric_strings_are_not_mangled():
    for value in ("-1", "-3.5", "1e3", "0", "42", ".5", "-.5"):
        assert csv_safe_cell(value) == value


def test_neutralizes_equals_formula():
    assert csv_safe_cell("=cmd|'/c calc'!A1") == "'=cmd|'/c calc'!A1"
    assert csv_safe_cell("=HYPERLINK(\"http://evil\")") == "'=HYPERLINK(\"http://evil\")"


def test_neutralizes_plus_at_and_leading_whitespace_formula():
    assert csv_safe_cell("@SUM(A1)") == "'@SUM(A1)"
    assert csv_safe_cell("+1+1+cmd()") == "'+1+1+cmd()"
    assert csv_safe_cell("   =1+1") == "'   =1+1"


def test_neutralizes_leading_tab_and_carriage_return():
    assert csv_safe_cell("\t=1+1") == "'\t=1+1"
    assert csv_safe_cell("\r=1+1") == "'\r=1+1"


def test_hyphen_prefixed_non_number_is_neutralized():
    assert csv_safe_cell("-2+3+cmd|'/C calc'!A0") == "'-2+3+cmd|'/C calc'!A0"


def test_empty_string_passes_through():
    assert csv_safe_cell("") == ""
