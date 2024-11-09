import pytest

from sensei import Manager, Client, Router, AsyncClient, RateLimit
from sensei.client.exceptions import CollectionLimitError


class TestClient:
    def test_manager_validation(self, sync_maker, base_maker, base_url):
        client = Client(base_url='https://google.com')
        aclient = AsyncClient(base_url='https://google.com')
        manager = Manager(client)

        with pytest.raises(CollectionLimitError):
            manager.set(client)

        manager.set(aclient)

        manager.pop()

        with pytest.raises(TypeError):
            manager.set(None)

        with pytest.raises(AttributeError):
            manager.pop()

        manager.get(is_async=True)
        manager.pop(is_async=True)

        with pytest.raises(AttributeError):
            manager.get()

        router = Router(host=base_url, manager=manager)
        base = base_maker(router)
        model = sync_maker(router, base)

        with pytest.raises(AttributeError):
            model.get(1)

        manager = Manager(required=False)

        router = Router(host=base_url, manager=manager)
        base = base_maker(router)
        model = sync_maker(router, base)

        model.get(1)

    def test_sync_manager(self, sync_maker, base_maker, base_url):
        client = Client(base_url=base_url)

        with client as client:
            manager = Manager(client)
            router = Router(host=base_url, manager=manager)

            base = base_maker(router)
            model = sync_maker(router, base)
            model.get(1)

        assert client.is_closed

    @pytest.mark.asyncio
    async def test_async_manager(self, async_maker, base_maker, base_url):
        client = AsyncClient(base_url=base_url)

        async with client as client:
            manager = Manager(async_client=client)
            router = Router(host=base_url, manager=manager)

            base = base_maker(router)
            model = async_maker(router, base)
            await model.get(1)  # type: ignore

        assert client.is_closed

    def test_rate_limit(self, base_url, sync_maker, base_maker):
        rate_limit = RateLimit(2, 1)
        router = Router(host=base_url, rate_limit=rate_limit)

        base = base_maker(router)
        model = sync_maker(router, base)

        model.get(1)
        assert rate_limit._tokens == 1

    @pytest.mark.asyncio
    async def test_async_rate_limit(self, base_url, async_maker, base_maker):
        rate_limit = RateLimit(2, 1)
        router = Router(host=base_url, rate_limit=rate_limit)

        base = base_maker(router)
        model = async_maker(router, base)

        await model.get(1)  # type: ignore
        assert rate_limit._tokens == 1
