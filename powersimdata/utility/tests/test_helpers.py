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


def test_cache_key_valid_types():
    key1 = cache_key(["foo", "bar"], 4, "other")
    assert (("foo", "bar"), 4, "other") == key1

    key2 = cache_key(True)
    assert (True,) == key2

    key3 = cache_key({1, 2, 2, 3})
    assert ((1, 2, 3),) == key3

    key4 = cache_key(None)
    assert ("null",) == key4


def test_no_collision():
    key1 = cache_key([["foo"], ["bar"]])
    key2 = cache_key([[["foo"], ["bar"]]])
    key3 = cache_key([["foo"], "bar"])
    keys = [key1, key2, key3]
    assert len(keys) == len(set(keys))


def test_cache_key_unsupported_type():
    with pytest.raises(ValueError):
        cache_key(object())


def test_cache_key_distinct_types():
    assert cache_key(4) != cache_key("4")


def test_mem_cache_put_dict():
    cache = MemoryCache()
    key = cache_key(["foo", "bar"], 4, "other")
    obj = {"key1": 42}
    cache.put(key, obj)
    assert cache.get(key) == obj


def test_mem_cache_get_returns_copy():
    cache = MemoryCache()
    key = cache_key("foo", 4)
    obj = {"key1": 42}
    cache.put(key, obj)
    assert id(cache.get(key)) != id(obj)


def test_mem_cache_put_version_never_changes():
    cache = MemoryCache()
    key = cache_key("foo", 4)
    obj = {"key1": "value1"}
    cache.put(key, obj)
    obj["key2"] = "value2"
    assert "key1" in cache.get(key)
    assert "key2" not in cache.get(key)
    assert "key2" in obj
