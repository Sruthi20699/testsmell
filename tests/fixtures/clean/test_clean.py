from unittest import mock

import pytest


def add(a, b):
    return a + b


def test_add():
    assert add(2, 3) == 5


def test_add_rejects_strings():
    with pytest.raises(TypeError):
        add(1, "a")


def test_mock_called():
    callback = mock.Mock()
    callback(1)
    callback.assert_called_once_with(1)


class TestAdd:
    def test_negative(self):
        assert add(-1, -1) == -2

    def test_is_none_check(self):
        result = None
        assert result is None
