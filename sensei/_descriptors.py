from sensei.types import IRateLimit


class RateLimitAttr:
    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: object, owner: type) -> IRateLimit:
        return obj.__dict__[self.name]

    def __set__(self, obj: object, value: IRateLimit) -> None:
        if value is None or isinstance(value, IRateLimit):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(f'Value must implement {IRateLimit} interface')


class PortAttr:
    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, obj: object, owner: type) -> IRateLimit:
        return obj.__dict__[self.name]

    def __set__(self, obj: object, value: IRateLimit) -> None:
        if value is None or isinstance(value, int) and 1 <= value <= 65535:
            obj.__dict__[self.name] = value
        else:
            raise ValueError('Port must be between 1 and 65535')