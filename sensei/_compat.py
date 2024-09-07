from pydantic.version import VERSION as P_VERSION

PYDANTIC_VERSION = P_VERSION
PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")

if PYDANTIC_V2:
    from pydantic_core import PydanticUndefined
    Undefined = PydanticUndefined
else:
    from pydantic.fields import Undefined
