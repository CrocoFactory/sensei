from collections.abc import Iterable
from typing import Protocol


class _NamedObj(Protocol):
    __name__ = ...


class CollectionLimitError(ValueError):
    def __init__(self, collection: _NamedObj, elements: Iterable[tuple[int, _NamedObj]]):
        super().__init__(
            f'{collection.__name__} size limit exceeded. '
            f'It can contain only '
            f'{", ".join([str(limit) + " " + cls.__name__ + ("s" if limit != 1 else "") for limit, cls in elements])}.'
        )
