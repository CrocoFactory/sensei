import time

import pytest
from sensei import Manager, Client, Router, AsyncClient, RateLimit
from sensei.client.exceptions import CollectionLimitError


class TestClient:
    def test_manager_validation(self):
        with pytest.raises(TypeError):
            manager = Manager(None)

        client = Client(host='https://google.com')
        manager = Manager(client)

        with pytest.raises(CollectionLimitError):
            manager.set(client)

        manager.pop()

        with pytest.raises(TypeError):
            manager.set(None)

        with pytest.raises(AttributeError):
            manager.pop()

        with pytest.raises(AttributeError):
            manager.get()

    def test_sync_manager(self, sync_maker, base_maker, base_url):
        client = Client(host=base_url)

        with client as client:
            manager = Manager(client)
            router = Router(host=base_url, manager=manager)

            base = base_maker(router)
            model = sync_maker(router, base)
            model.get(1)

        assert client.is_closed

    @pytest.mark.asyncio
    async def test_async_manager(self, async_maker, base_maker, base_url):
        client = AsyncClient(host=base_url)

        async with client as client:
            manager = Manager(client)
            router = Router(host=base_url, manager=manager)

            base = base_maker(router)
            model = async_maker(router, base)
            await model.get(1)  # type: ignore

        assert client.is_closed

    def test_client_validation(self):
        client = Client(host='https://google.com')
        with pytest.raises(AttributeError):
            client.port = 3000

        with pytest.raises(ValueError):
            client1 = Client(host='https://google.com', port=-2000)

        with pytest.raises(TypeError):
            client = Client(host='https://google.com', rate_limit='hello')

    def test_formatting(self):
        client = Client(host='https://domain.com:{port}/sumdomain', port=3000)
        assert str(client.base_url) == 'https://domain.com:3000/sumdomain/'

    def test_rate_limit(self, base_url, sync_maker, base_maker):
        rate_limit = RateLimit(2, 1)
        router = Router(host=base_url, rate_limit=rate_limit)

        base = base_maker(router)
        model = sync_maker(router, base)

        now = time.time()
        model.get(1)
        assert rate_limit._tokens == 1
        model.get(2)

        model.get(3)
        model.get(4)

        assert time.time() - now >= 2

    @pytest.mark.asyncio
    async def test_async_rate_limit(self, base_url, async_maker, base_maker):
        rate_limit = RateLimit(2, 1)
        router = Router(host=base_url, rate_limit=rate_limit)

        base = base_maker(router)
        model = async_maker(router, base)

        now = time.time()
        await model.get(1)  # type: ignore
        assert rate_limit._tokens == 1
        await model.get(2)  # type: ignore

        await model.get(3)  # type: ignore
        await model.get(4)  # type: ignore

        assert time.time() - now >= 2
