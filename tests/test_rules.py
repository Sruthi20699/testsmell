from testsmell.rules import REGISTRY


def lines(rule_id, module):
    return [f.line for f in REGISTRY[rule_id].check(module)]


# TS001 no assertion


def test_ts001_flags_test_without_assertion(module_from):
    m = module_from(
        "def test_a():\n    x = 1\n\nclass TestB:\n    def test_c(self):\n        pass\n"
    )
    assert lines("TS001", m) == [1, 5]


def test_ts001_accepts_other_ways_of_asserting(module_from):
    m = module_from(
        "import pytest\n"
        "def test_raises():\n    with pytest.raises(ValueError):\n        int('x')\n"
        "def test_mock(m):\n    m.assert_called_once()\n"
        "def test_unittest(self):\n    self.assertEqual(1, 1)\n"
        "def test_fail():\n    pytest.fail('boom')\n"
    )
    assert lines("TS001", m) == []


def test_ts001_ignores_helpers(module_from):
    m = module_from("def make_user():\n    return 1\n")
    assert lines("TS001", m) == []


# TS002 always-true assert


def test_ts002_flags_tuple_and_constant_asserts(module_from):
    m = module_from(
        "def test_a():\n"
        "    assert (1 == 2, 'msg')\n"
        "    assert 'not empty'\n"
        "    assert True\n"
        "    assert 1 == 2, 'msg'\n"
        "    assert ()\n"
        "    assert 0\n"
    )
    assert lines("TS002", m) == [2, 3, 4]


# TS003 sleep


def test_ts003_flags_sleep_calls_in_tests_only(module_from):
    m = module_from(
        "import time\nfrom time import sleep\n"
        "def wait():\n    time.sleep(1)\n"
        "def test_a():\n    time.sleep(1)\n    sleep(0.5)\n    assert True\n"
    )
    assert lines("TS003", m) == [6, 7]


# TS004 duplicate names


def test_ts004_flags_redefined_tests_per_scope(module_from):
    m = module_from(
        "def test_a():\n    assert 1\n"
        "def test_a():\n    assert 1\n"
        "class TestX:\n"
        "    def test_a(self):\n        assert 1\n"
        "    def test_a(self):\n        assert 1\n"
        "class TestY:\n"
        "    def test_a(self):\n        assert 1\n"
    )
    findings = list(REGISTRY["TS004"].check(m))
    assert [f.line for f in findings] == [3, 8]
    assert "first on line 1" in findings[0].message
    assert "TestX.test_a" in findings[1].message


# TS005 swallowed failures


def test_ts005_flags_broad_silent_handlers(module_from):
    m = module_from(
        "def test_a():\n"
        "    try:\n        assert 1 == 2\n    except:\n        pass\n"
        "    try:\n        assert 1 == 2\n    except Exception:\n        ...\n"
        "    try:\n        int('x')\n    except ValueError:\n        pass\n"
        "    try:\n        assert 1\n    except AssertionError:\n        raise\n"
    )
    findings = list(REGISTRY["TS005"].check(m))
    assert [f.line for f in findings] == [4, 8]
    assert "catches everything" in findings[0].message


# TS006 == None/True/False


def test_ts006_flags_equality_with_singletons(module_from):
    m = module_from(
        "def test_a(x):\n"
        "    assert x == None\n"
        "    assert x != True\n"
        "    assert None == x\n"
        "    assert x is None\n"
        "    assert x == 0\n"
    )
    assert lines("TS006", m) == [2, 3, 4]
