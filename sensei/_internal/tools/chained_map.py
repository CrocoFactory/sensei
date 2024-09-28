from collections.abc import Mapping
from typing import Iterator, TypeVar, Any, Hashable

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')


class ChainedMap(Mapping[_KT, _VT]):
    def __init__(self, *dicts: dict[Any, Any]) -> None:
        self._dicts: tuple[dict[Any, Any], ...] = dicts

    def __getitem__(self, key: _KT) -> _VT:
        for d in self._dicts:
            if key in d:
                value = d[key]
                if any(value in next_d for next_d in self._dicts if isinstance(value, Hashable) and next_d is not d):
                    return self.__getitem__(value)
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[Any]:
        for key in self._dicts[0]:
            yield from self.trace(key)

    def __len__(self) -> int:
        unique_keys = {key for d in self._dicts for key in d}
        return len(unique_keys)

    def trace(self, key: _KT) -> Iterator[Any]:
        """Yields the key and follows its chain through the dictionaries."""
        seen = []

        current_value = key
        while True:
            if current_value in seen:
                break
            seen.append(current_value)
            yield current_value
            for d in self._dicts:
                try:
                    if current_value in d:
                        current_value = d[current_value]
                        break
                except TypeError:
                    pass
            else:
                break
