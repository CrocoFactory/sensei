from typing import Any


class CollectionLimitError(Exception):
    def __init__(self, collection: Any, limit: int, element_name: str = "element"):
        super().__init__(
            f'{collection} size limit exceeded. '
            f'It can contain only {limit} {element_name.lower()}{"s" if limit != 1  else ""}.'
        )
