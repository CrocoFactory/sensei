import json
from abc import ABC, abstractmethod
from httpx import Response
from typing_extensions import Self
from sensei import Args


class Endpoint(ABC):
    endpoints: list[type[Self]] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Endpoint.endpoints.append(cls)

    @staticmethod
    @abstractmethod
    def responser(args: Args) -> Response:
        pass

    @staticmethod
    @abstractmethod
    def args() -> list[Args]:
        pass

    @staticmethod
    @abstractmethod
    def method() -> str:
        pass

    @staticmethod
    @abstractmethod
    def url() -> str:
        pass


class GetUser(Endpoint):
    @staticmethod
    def responser(args: Args) -> Response:
        """
        Simulates fetching a user by ID.
        """
        user_id = args.params.get('id', 'unknown')
        data = {'id': user_id, 'name': 'John Doe'}
        content = json.dumps(data).encode('utf-8')
        return Response(status_code=200, content=content)

    @staticmethod
    def args() -> list[Args]:
        return [
            Args(
                url="http://api.example.com/users/1",
                params={'id': '1'},
                json={}
            )
        ]

    @staticmethod
    def method() -> str:
        return "GET"

    @staticmethod
    def url() -> str:
        return "http://api.example.com/users/1"


class CreateUser(Endpoint):
    @staticmethod
    def responser(args: Args) -> Response:
        """
        Simulates creating a new user.
        """
        user_data = args.json_
        user_data['id'] = 123  # Simulate assigning an ID
        content = json.dumps(user_data).encode('utf-8')
        return Response(status_code=201, content=content)

    @staticmethod
    def args() -> list[Args]:
        return [
            Args(
                url="http://api.example.com/users",
                params={},
                json={'name': 'Charlie'}
            )
        ]

    @staticmethod
    def method() -> str:
        return "POST"

    @staticmethod
    def url() -> str:
        return "http://api.example.com/users"


class UpdateUser(Endpoint):
    @staticmethod
    def responser(args: Args) -> Response:
        """
        Simulates updating an existing user.
        """
        user_id = args.params.get('id', 'unknown')
        user_data = args.json_
        user_data['id'] = user_id
        content = json.dumps(user_data).encode('utf-8')
        return Response(status_code=200, content=content)

    @staticmethod
    def args() -> list[Args]:
        return [
            Args(
                url="http://api.example.com/users/1",
                params={'id': '1'},
                json={'name': 'Alice Updated'}
            )
        ]

    @staticmethod
    def method() -> str:
        return "PUT"

    @staticmethod
    def url() -> str:
        return "http://api.example.com/users/1"


class DeleteUser(Endpoint):
    @staticmethod
    def responser(args: Args) -> Response:
        """
        Simulates deleting a user.
        """
        return Response(status_code=204)

    @staticmethod
    def args() -> list[Args]:
        return [
            Args(
                url="http://api.example.com/users/2",
                params={'id': '2'},
                json={}
            )
        ]

    @staticmethod
    def method() -> str:
        return "DELETE"

    @staticmethod
    def url() -> str:
        return "http://api.example.com/users/2"


class ListUsers(Endpoint):
    @staticmethod
    def responser(args: Args) -> Response:
        """
        Simulates listing all users.
        """
        users = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ]
        content = json.dumps(users).encode('utf-8')
        return Response(status_code=200, content=content)

    @staticmethod
    def args() -> list[Args]:
        return [
            Args(
                url="http://api.example.com/users",
                params={},
                json={}
            )
        ]

    @staticmethod
    def method() -> str:
        return "GET"

    @staticmethod
    def url() -> str:
        return "http://api.example.com/users"


class GetStatus(Endpoint):
    @staticmethod
    def responser(args: Args) -> Response:
        """
        Simulates fetching the service status.
        """
        status = {'status': 'ok'}
        content = json.dumps(status).encode('utf-8')
        return Response(status_code=200, content=content)

    @staticmethod
    def args() -> list[Args]:
        return [
            Args(
                url="http://api.example.com/status",
                params={},
                json={}
            )
        ]

    @staticmethod
    def method() -> str:
        return "GET"

    @staticmethod
    def url() -> str:
        return "http://api.example.com/status"
