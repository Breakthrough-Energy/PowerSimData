import pytest

from powersimdata.utility.helpers import MemoryCache, PrintManager, cache_key


def test_print_is_disabled(capsys):
    pm = PrintManager()
    pm.block_print()
    print("printout are disabled")
    captured = capsys.readouterr()
    assert captured.out == ""

    pm.enable_print()
    print("printout are enabled")
    captured = capsys.readouterr()
    assert captured.out == "printout are enabled\n"


def test_cache_key_types():
    key1 = cache_key(["foo", "bar"], 4, "other")
    assert ("foo-bar", "4", "other") == key1

    key2 = cache_key(True)
    assert ("True",) == key2

    key3 = cache_key({1, 2, 2, 3})
    assert ("1-2-3",) == key3


def test_cache_key_unsupported_type():
    with pytest.raises(ValueError):
        cache_key(object)


def test_mem_cache_put_dict():
    cache = MemoryCache()
    first = cache_key(["foo", "bar"], 4, "other")
    obj = {"key1": 42}
    cache.put(first, obj)
    assert cache.get(first) == obj
