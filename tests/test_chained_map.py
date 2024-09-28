import pytest
from sensei._internal.tools import ChainedMap


class TestChainedMap:
    def test_getitem_simple(self):
        """Test __getitem__ with simple keys."""
        cm = ChainedMap({'a': 1, 'b': 2})
        assert cm['a'] == 1
        assert cm['b'] == 2

    def test_getitem_chain(self):
        """Test __getitem__ with chained keys."""
        cm = ChainedMap({'a': 'b'}, {'b': 'c'}, {'c': 3})
        assert cm['a'] == 3  # 'a' -> 'b' -> 'c' -> 3

    def test_getitem_missing(self):
        """Test __getitem__ when the key is missing."""
        cm = ChainedMap({'a': 1})
        with pytest.raises(KeyError):
            _ = cm['nonexistent']

    def test_getitem_with_loop(self):
        """Test __getitem__ when there is a loop in the key chain."""
        cm = ChainedMap({'a': 'b'}, {'b': 'a'})
        with pytest.raises(RecursionError):
            _ = cm['a']

    def test_getitem_no_chain(self):
        """Test __getitem__ when there is no further chaining."""
        cm = ChainedMap({'a': 'b'}, {'c': 'd'})
        assert cm['a'] == 'b'  

    def test_getitem_value_in_later_dict(self):
        """Test __getitem__ when the value is in a later dictionary."""
        cm = ChainedMap({'a': 'b'}, {'b': 2})
        assert cm['a'] == 2  # 'a' -> 'b' -> 2

    def test_getitem_value_in_previous_dict(self):
        """Test __getitem__ when the value is in a previous dictionary."""
        cm = ChainedMap({'b': 2}, {'a': 'b'})
        assert cm['a'] == 2  # 'a' -> 'b' -> 2

    def test_len(self):
        """Test __len__ method."""
        cm = ChainedMap({'a': 1, 'b': 2}, {'c': 3})
        assert len(cm) == 3

    def test_len_with_duplicate_keys(self):
        """Test __len__ with duplicate keys in different dictionaries."""
        cm = ChainedMap({'a': 1}, {'a': 2}, {'b': 3})
        assert len(cm) == 2

    def test_iter(self):
        """Test __iter__ method."""
        cm = ChainedMap({'a': 'b'}, {'b': 'c'}, {'c': 3})
        keys = list(cm)
        assert keys == ['a', 'b', 'c', 3]

    def test_iter_with_duplicate_keys(self):
        """Test __iter__ with duplicate keys."""
        cm = ChainedMap({'a': 1}, {'a': 2}, {'b': 3})
        keys = list(cm)
        assert keys == ['a', 1]

    def test_trace(self):
        """Test the trace method."""
        cm = ChainedMap({'a': 'b'}, {'b': 'c'}, {'c': 3})
        trace_a = list(cm.trace('a'))
        assert trace_a == ['a', 'b', 'c', 3]

    def test_trace_with_unhashable_value(self):
        """Test trace when the value is unhashable."""
        cm = ChainedMap({'a': ['list']})
        trace_a = list(cm.trace('a'))
        assert trace_a == ['a', ['list']]
