from typing import Optional

from httpx._client import Client, AsyncClient, BaseClient

from .exceptions import CollectionLimitError


class Manager:
    __slots__ = ('_sync_client', '_async_client', '_required')

    def __init__(
            self,
            sync_client: Optional[Client] = None,
            async_client: Optional[AsyncClient] = None,
            *,
            required: bool = True,
    ) -> None:
        """
        This class serves as a bridge between the application and Sensei, to dynamically provide a client for
        routed function calls.
        It separately stores `httpx.AsyncClient` and `httpx.Client`.
        To use `Manager`, you need to create it and pass it to the router.

        Import it directly from Sensei:

        ```python
        from sensei import Manager
        ```

        Example:
            ```python
            from sensei import Manager, Router, Client

            manager = Manager()
            router = Router('httpx://example-api.com', manager=manager)

            @router.get('/users/{id_}')
            def get_user(id_: int) -> User:
                pass

            with Client(base_url=router.base_url) as client:
                manager.set(client)
                user = get_user(1)
                print(user)
                manager.pop()
            ```

        Args:
            sync_client (Client): An instance of `httpx.Client`.
            async_client (AsyncClient): An instance of `httpx.AsyncClient`.
            required (bool): Whether to throw the error in `get` if a client is not set

        Raises:
            TypeError: If the provided client is not an instance of AsyncClient or Client.
        """
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
        Set a client instance in the manager if no client is currently set. If a client of the provided type is
        already set, it raises a `CollectionLimitError`.

        Example:
            ```python
            from sensei import Manager, Router, Client, AsyncClient

            manager = Manager()
            router = Router('httpx://example-api.com', manager=manager)

            client = Client(base_url=router.base_url)
            aclient = AsyncClient(base_url=router.base_url)

            manager.set(client)
            manager.set(aclient)
            ```

        Args:
            client (BaseClient): The client instance to set.

        Raises:
            CollectionLimitError: If a client of the provided type is already set.
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

        Example:
            ```python
            manager = Manager()

            manager = Manager(sync_client=client, async_client=aclient)
            client = manager.pop(is_async=False)
            aclient = manager.pop(is_async=True)
            print(client, aclient)
            ```

        Args:
            is_async (bool): Whether client instance is async

        Returns:
            BaseClient: The client instance that was managed.

        Raises:
            AttributeError: If no client is set.
        """
        set_client = self._get_client(is_async, True, True)
        return set_client

    def empty(self, is_async: bool = False) -> bool:
        """
        Check if the manager has a client of the provided type set.

        Example:
            ```python
            manager = Manager()

            manager = Manager(sync_client=client)
            manager.pop()
            print(manager.empty()) # Output: True
            ```

        Args:
            is_async (bool): Whether client instance is async

        Returns:
            bool: True if no client is set, False otherwise.
        """
        set_client = self._get_client(is_async)

        return set_client is None

    def get(self, is_async: bool = False) -> BaseClient:
        """
        Retrieve the currently set client of the provided type.
        This method returns the managed client without removing it.

        Example:
            ```python
            manager = Manager()

            manager = Manager(sync_client=client, async_client=aclient)
            client = manager.get(is_async=False)
            aclient = manager.get(is_async=True)
            print(client, aclient)
            ```

        Args:
            is_async (bool): Whether client instance is async

        Returns:
            BaseClient: The client instance that is being managed.

        Raises:
            AttributeError: If no client is set.
        """
        set_client = self._get_client(is_async, required=self._required)

        return set_client
