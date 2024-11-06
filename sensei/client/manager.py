from typing import Optional

from httpx._client import Client, AsyncClient, BaseClient

from .exceptions import CollectionLimitError


class Manager:
    """
    A generic manager class for handling a single client instance of each type (async/sync).

    This class manages an instance of a client (which must be a subclass of `BaseClient`),
    ensuring that only one client is set at a time. The class provides methods to set,
    pop, and check the presence of the client.

    Args:
        sync_client (Client): An instance of `httpx.Client`.
        async_client (AsyncClient): An instance of `httpx.AsyncClient`.
        required (bool): Whether to throw the error in `get`, if a client is not set
    Raises:
        ValueError: If the provided client is not an instance of `BaseClient`.
    """

    __slots__ = ('_sync_client', '_async_client', '_required')

    def __init__(
            self,
            sync_client: Optional[Client] = None,
            async_client: Optional[AsyncClient] = None,
            *,
            required: bool = True,
    ) -> None:
        self._sync_client = self._validate_client(sync_client, True)
        self._async_client = self._validate_client(async_client, True, True)
        self._required = required

    @staticmethod
    def _validate_client(client: BaseClient, nullable: bool = False, is_async: bool = False) -> Optional[BaseClient]:
        if nullable and client is None:
            return client
        elif is_async and not isinstance(client, AsyncClient):
            raise TypeError(f"Client must be an instance of {AsyncClient}.")
        elif not is_async and not isinstance(client, Client):
            raise TypeError(f"Client must be an instance of {Client}.")

        return client

    def _get_client(self, is_async: bool, pop: bool = False, required: bool = False) -> Optional[BaseClient]:
        if is_async:
            set_client = self._async_client
            if pop:
                self._async_client = None
        else:
            set_client = self._sync_client
            if pop:
                self._sync_client = None

        if set_client is None and required:
            client_type = AsyncClient if is_async else Client
            raise AttributeError(f"{client_type} is not set")

        return set_client

    def set(self, client: BaseClient) -> None:
        """
        Set a client instance in the manager.

        This method sets the client if no client is currently set. If a client is
        already set, it raises a `CollectionLimitError`.

        Args:
            client (BaseClient): The client instance to set.

        Raises:
            CollectionLimitError: If a client is already set.
            TypeError: If the provided client is not an instance of AsyncClient or Client.
        """
        is_async = isinstance(client, AsyncClient)
        set_client = self._get_client(is_async)

        if set_client is None:
            if is_async:
                self._async_client = self._validate_client(client, is_async=True)
            else:
                self._sync_client = self._validate_client(client)
        else:
            raise CollectionLimitError(self.__class__, [(1, Client), (1, AsyncClient)])

    def pop(self, is_async: bool = False) -> BaseClient:
        """
        Remove and return the currently set client.

        This method removes the managed client and returns it. After calling this method,
        the manager will no longer have a client set. But the client type defined at creation is not reset.

        Args:
            is_async (bool): Whether client instance is async

        Returns:
            _Client: The client instance that was managed.

        Raises:
            AttributeError: If no client is set.
        """
        set_client = self._get_client(is_async, True, True)
        return set_client

    def empty(self, is_async: bool = False) -> bool:
        """
        Check if the manager has a client set.

        Args:
            is_async (bool): Whether client instance is async

        Returns:
            bool: True if no client is set, False otherwise.
        """
        set_client = self._get_client(is_async)

        return set_client is None

    def get(self, is_async: bool = False) -> BaseClient:
        """
        Retrieve the currently set client.
        This method returns the managed client without removing it.

        Args:
            is_async (bool): Whether client instance is async

        Returns:
            _Client: The client instance that is being managed.

        Raises:
            AttributeError: If no client is set.
        """
        set_client = self._get_client(is_async, required=self._required)

        return set_client
