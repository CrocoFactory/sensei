from __future__ import annotations

import json
import base64
import pickle
from enum import Enum
from typing import Iterator, Mapping, Callable
from httpx import Response
from typing_extensions import Self
from sensei import Args, Json
from pydantic import AnyHttpUrl, BaseModel

Responser = Callable[[Args], Response]

Signature = tuple[str, str]
TestData = tuple[Responser, list[Args]]


class _HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD",
    OPTIONS = "OPTIONS"
    CONNECT = "CONNECT"
    TRACE = "TRACE"

    def __str__(self) -> str:
        return self.value


class MockDataset(Mapping[Signature, TestData]):
    """
    A class to represent a dataset for mocking HTTP responses.

    This class implements the Mapping interface, allowing it to be used like a dictionary
    where keys are tuples of HTTP method and URL, and values are test data consisting
    of a responser callable and a list of Args instances.

    >>> def send_response(args: Args) -> Response:
    ...     params = args.params
    ...
    ...     fullname = params['name'] + " " + params['surname']
    ...     json_ = {'fullname': fullname}
    ...     dumped = json.dumps(json_)
    ...     return Response(200, content=dumped)
    ...
    >>> url = "http://url.com"
    >>> data = [Args(url=url, params={'name': 'John', 'surname': "Gold"})]
    >>> dataset = MockDataset()
    >>> dataset["GET", url] = send_response, data
    >>> dumped = dataset.dumps()
    >>> new_dataset = MockDataset.loads(dumped)
    >>> new_dataset == dataset
    True
    """

    def __init__(self):
        self._data: dict[Signature, TestData] = {}

    def __len__(self) -> int:
        """
        Returns the number of items in the dataset.

        Returns:
            int: The number of key-value pairs in the dataset.
        """
        return len(self._data)

    def __contains__(self, item: Signature) -> bool:
        """
        Checks if a given signature is in the dataset.

        Args:
            item (Signature): A tuple containing the HTTP method and URL.

        Returns:
            bool: True if the signature exists, False otherwise.
        """
        return item in self._data

    def __iter__(self) -> Iterator[Signature]:
        """
        Returns an iterator over the dataset's keys.

        Returns:
            Iterator[Signature]: An iterator of signatures.
        """
        return iter(self._data)

    def __getitem__(self, item: Signature) -> TestData:
        """
        Retrieves the test data associated with a given signature.

        Args:
            item (Signature): A tuple containing the HTTP method and URL.

        Returns:
            TestData: A tuple of responser and list of Args.

        Raises:
            KeyError: If the signature is not found in the dataset.
        """
        return self.get_responser(*item)

    def __setitem__(self, item: Signature, test_data: TestData) -> None:
        """
        Sets the test data for a given signature in the dataset.

        Args:
            item (Signature): A tuple containing the HTTP method and URL.
            test_data (TestData): A tuple of responser and list of Args.
        """
        self.add_responser(*item, *test_data)

    def __eq__(self, other: MockDataset) -> bool:
        """
        Checks equality with another MockDataset instance.

        Args:
            other (MockDataset): Another instance to compare with.

        Returns:
            bool: True if both datasets are equal, False otherwise.
        """
        return self._data == other._data

    def add_responser(
            self,
            method: str,
            url: str,
            responser: Responser,
            args: list[Args]
    ) -> None:
        """
        Adds a mock response for a specific HTTP method and URL.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST').
            url (str): The URL to mock.
            responser (Responser): A callable that returns an HTTP response.
            args (list[Args]): A list of Args instances associated with the response.

        Raises:
            pydantic_core.ValidationError: If the provided data does not conform to the validation model.
        """

        class _ValidationModel(BaseModel):
            method: _HTTPMethod
            url: AnyHttpUrl
            responser: Responser
            args: list[Args]

        _ValidationModel(method=method, url=url, responser=responser, args=args)  # type: ignore

        key = method.upper(), url
        self._data[key] = responser, args

    def get_responser(self, method: str, url: str) -> TestData:
        """
        Retrieves the responser and args for a given HTTP method and URL.

        Args:
            method (str): The HTTP method.
            url (str): The URL.

        Returns:
            TestData: A tuple of responser and list of Args.

        Raises:
            KeyError: If no mock data is found for the specified method and URL.
        """
        key = method.upper(), url
        if key not in self._data:
            raise KeyError(f"No mock data found for {method} {url}")

        test_data = self._data[key]
        return test_data

    @classmethod
    def load(cls, filepath: str) -> Self:
        """
        Loads a MockDataset from a JSON file.

        Args:
            filepath (str): The path to the JSON file containing the dataset.

        Returns:
            MockDataset: An instance of MockDataset populated with the loaded data.
        """
        with open(filepath, 'r') as f:
            loaded_data = json.load(f)

        return cls.loads(loaded_data)

    @classmethod
    def loads(cls, data: Json) -> Self:
        """
        Loads a MockDataset from a JSON-compatible data structure.

        Args:
            data (Json): The JSON data representing the dataset.

        Returns:
            MockDataset: An instance of MockDataset populated with the loaded data.
        """
        dataset = cls()

        for entry in data:
            url = entry["url"]
            responser_encoded = entry["responser"]

            try:
                responser_bytes = base64.b64decode(responser_encoded)
                responser = pickle.loads(responser_bytes)
            except pickle.PickleError as e:
                raise ValueError(f"Failed to decode and unpickle responser for {entry['method']} {url}: {e}")

            dataset.add_responser(
                method=entry["method"],
                url=url,
                responser=responser,
                args=[Args(url=url, **value) for value in entry["args"]]
            )

        return dataset

    def dumps(self) -> Json:
        """
        Serializes the MockDataset to a JSON-compatible format.

        Returns:
            Json: The serialized dataset.
        """
        data = self._data

        dumped = []

        for signature, test_data in data.items():
            method, url = signature
            responser, args = test_data

            pickled_responser = pickle.dumps(responser)
            responser = base64.b64encode(pickled_responser).decode('utf-8')

            def _remove_url(value: dict) -> dict:
                """
                Removes the 'url' key from the args dictionary.

                Args:
                    value (dict): The args dictionary.

                Returns:
                    dict: The modified dictionary without the 'url' key.
                """
                value.pop('url')
                return value

            args = [_remove_url(value.model_dump(mode="json")) for value in args]
            dumped.append({'method': method, 'url': url, 'responser': responser, 'args': args})

        return dumped

    def dump(self, filepath: str) -> None:
        """
        Serializes the MockDataset to a JSON-compatible format and write it to a file.

        Args:
            filepath (str): The path to the JSON file containing the dataset.
        """
        result = self.dumps()

        with open(filepath, 'w') as f:
            f.write(json.dumps(result))
