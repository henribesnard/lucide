import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.utils.status_mapping import get_status_info, is_valid_status, load_status_table


def test_status_table_is_loaded():
    table = load_status_table()
    assert table, "status table should not be empty"
    assert "FT" in table


def test_get_status_info_normalizes_code():
    info = get_status_info("ft")
    assert info["code"] == "FT"
    assert info["label"]


def test_unknown_status_is_flagged():
    info = get_status_info("XXX")
    assert info["code"] == "XXX"
    assert info["type"] in ("Unknown", None)
    assert not is_valid_status("XXX")
