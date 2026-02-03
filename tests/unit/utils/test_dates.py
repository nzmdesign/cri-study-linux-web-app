import pytest
from datetime import datetime

from utils.dates import to_jst

class TestToJst:
    """to_jst関数のテスト"""

    def test_converts_correctly(self):
        """UTC時間をJSTに正しく変換することを確認する"""
        utc_time = datetime(2026, 2, 3, 10, 0, 0)
        result = to_jst(utc_time)
        assert result == datetime(2026, 2, 3, 19, 0, 0)

    def test_crosses_day(self):
        """UTC時間が日付を跨ぐ場合のJST変換を確認する"""
        utc_time = datetime(2026, 2, 3, 15, 0, 0)
        result = to_jst(utc_time)
        assert result == datetime(2026, 2, 4, 0, 0, 0)

    def test_crosses_month(self):
        """UTC時間が月を跨ぐ場合のJST変換を確認する"""
        utc_time = datetime(2026, 1, 31, 16, 0, 0)
        result = to_jst(utc_time)
        assert result == datetime(2026, 2, 1, 1, 0, 0)

    def test_with_none_raises_error(self):
        """Noneが渡された場合に例外が発生することを確認する"""
        with pytest.raises(TypeError):
            to_jst(None)