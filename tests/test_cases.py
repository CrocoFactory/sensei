import pytest
from sensei import snake_case, camel_case, pascal_case, constant_case, kebab_case, header_case


class TestCases:
    @pytest.fixture(scope='class')
    def strings(self):
        return [
            "snake_case",
            "camelCase",
            "PascalCase",
            "CONSTANT_CASE",
            "kebab-case",
            "Header-Case",
            "weird_Case",
            "Weird_CASE"
        ]

    def test_snake_case(self, strings):
        result = [snake_case(s) for s in strings]
        assert result == [
            "snake_case",
            "camel_case",
            "pascal_case",
            "constant_case",
            "kebab_case",
            "header_case",
            "weird_case",
            "weird_case"
        ]

    def test_camel_case(self, strings):
        result = [camel_case(s) for s in strings]
        assert result == [
            "snakeCase",
            "camelCase",
            "pascalCase",
            "constantCase",
            "kebabCase",
            "headerCase",
            "weirdCase",
            "weirdCase"
        ]

    def test_pascal_case(self, strings):
        result = [pascal_case(s) for s in strings]
        assert result == [
            "SnakeCase",
            "CamelCase",
            "PascalCase",
            "ConstantCase",
            "KebabCase",
            "HeaderCase",
            "WeirdCase",
            "WeirdCase"
        ]

    def test_constant_case(self, strings):
        result = [constant_case(s) for s in strings]
        assert result == [
            "SNAKE_CASE",
            "CAMEL_CASE",
            "PASCAL_CASE",
            "CONSTANT_CASE",
            "KEBAB_CASE",
            "HEADER_CASE",
            "WEIRD_CASE",
            "WEIRD_CASE"
        ]

    def test_kebab_case(self, strings):
        result = [kebab_case(s) for s in strings]

        assert result == [
            "snake-case",
            "camel-case",
            "pascal-case",
            "constant-case",
            "kebab-case",
            "header-case",
            "weird-case",
            "weird-case"
        ]

    def test_header_case(self, strings):
        result = [header_case(s) for s in strings]

        assert result == [
            "Snake-Case",
            "Camel-Case",
            "Pascal-Case",
            "Constant-Case",
            "Kebab-Case",
            "Header-Case",
            "Weird-Case",
            "Weird-Case"
        ]