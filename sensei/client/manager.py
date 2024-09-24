from typing import TypeVar, Generic, Union
from sensei._base_client import BaseClient
from .exceptions import CollectionLimitError

_Client = TypeVar('_Client', bound=BaseClient)
_ClientToInstantiate = Union[type[_Client], _Client]


class Manager(Generic[_Client]):
    __slots__ = ('_client', '_client_type')

    def __init__(self, client: _Client):
        if isinstance(client, BaseClient):
            self._client = client
            self._client_type = type(client)
        else:
            raise ValueError("Client must be an instance either of AsyncClient or Client. Also can be provided type "
                             "AsyncClient or Client.")

    def set(self, client: _Client) -> None:
        if isinstance(client, self._client_type):
            if self._client is None:
                self._client = client
            else:
                raise CollectionLimitError(self.__class__, 1, "Client")
        else:
            raise TypeError(f"Client must be an instance of {self._client_type.__name__}")

    def pop(self) -> _Client:
        if self._client is None:
            raise AttributeError("Client is not set")
        else:
            client = self._client
            self._client = None
            return client

    def empty(self) -> bool:
        return self._client is None

    def get(self) -> _Client:
        if self._client is None:
            raise AttributeError("Client is not set")
        else:
            return self._client
