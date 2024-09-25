from typing import TypeVar, Generic
from sensei._base_client import BaseClient
from .exceptions import CollectionLimitError

_ClientType = TypeVar('_ClientType', bound=BaseClient)


class Manager(Generic[_ClientType]):
    """
    A generic manager class for handling a single client instance with type safety. The client type defined at creation
    and it`s not reset.

    This class manages an instance of a client (which must be a subclass of `BaseClient`),
    ensuring that only one client is set at a time. The class provides methods to set,
    pop, and check the presence of the client.

    Args:
        client (_Client): An instance of a class that extends `BaseClient`.

    Raises:
        ValueError: If the provided client is not an instance of `BaseClient`.
    """

    __slots__ = ('_client', '_client_type')

    def __init__(self, client: _ClientType):
        if isinstance(client, BaseClient):
            self._client = client
            self._client_type = type(client)
        else:
            raise ValueError(
                "Client must be an instance of AsyncClient or Client. "
                "Alternatively, provide the type 'AsyncClient' or 'Client' to instantiate the corresponding Manager."
            )

    def set(self, client: _ClientType) -> None:
        """
        Set a client instance in the manager.

        This method sets the client if no client is currently set. If a client is
        already set, it raises a `CollectionLimitError`.

        Args:
            client (_Client): The client instance to set.

        Raises:
            CollectionLimitError: If a client is already set.
            TypeError: If the provided client is not an instance of the same type as the current client.
        """
        if isinstance(client, self._client_type):
            if self._client is None:
                self._client = client
            else:
                raise CollectionLimitError(self.__class__, 1, "Client")
        else:
            raise TypeError(f"Client must be an instance of {self._client_type.__name__}")

    def pop(self) -> _ClientType:
        """
        Remove and return the currently set client.

        This method removes the managed client and returns it. After calling this method,
        the manager will no longer have a client set. But the client type defined at creation is not reset.

        Returns:
            _Client: The client instance that was managed.

        Raises:
            AttributeError: If no client is set.
        """
        if self._client is None:
            raise AttributeError("Client is not set")
        else:
            client = self._client
            self._client = None
            return client

    def empty(self) -> bool:
        """
        Check if the manager has a client set.

        Returns:
            bool: True if no client is set, False otherwise.
        """
        return self._client is None

    def get(self) -> _ClientType:
        """
        Retrieve the currently set client.

        This method returns the managed client without removing it.

        Returns:
            _Client: The client instance that is being managed.

        Raises:
            AttributeError: If no client is set.
        """
        if self._client is None:
            raise AttributeError("Client is not set")
        else:
            return self._client
