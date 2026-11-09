import time


def test_no_assert():
    value = 1 + 1
    print(value)


def test_tuple_assert():
    assert (1 == 2, "never fails")


def test_sleeps():
    time.sleep(2)
    assert time.time() > 0


def test_duplicate():
    assert 1 == 1


def test_duplicate():
    assert 2 == 2


def test_swallows_failure():
    try:
        assert 1 == 2
    except AssertionError:
        pass


def test_none_compare():
    result = None
    assert result == None


class TestThing:
    def test_method_without_assert(self):
        self.value = 3
