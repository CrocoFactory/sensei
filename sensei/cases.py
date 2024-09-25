import re

__all__ = [
    'snake_case',
    'camel_case',
    'pascal_case',
    'constant_case',
    'kebab_case',
    'header_case'
]


def snake_case(s: str) -> str:
    """Convert a string to snake_case. """
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'\W+', '_', s).lower()
    s = re.sub(r'_+', '_', s)
    return s


def camel_case(s: str) -> str:
    """Convert a string to camelCase."""
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'\W+', '_', s)
    words = s.split('_')
    capitalized_words = [word.capitalize() for word in words]
    return capitalized_words[0].lower() + ''.join(capitalized_words[1:])


def pascal_case(s: str) -> str:
    """Convert a string to PascalCase."""
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'\W+', '_', s)
    words = s.split('_')
    capitalized_words = [word.capitalize() for word in words]
    return ''.join(capitalized_words)


def constant_case(s: str) -> str:
    """Convert a string to CONSTANT_CASE."""
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'\W+', '_', s)
    return s.upper()


def kebab_case(s: str) -> str:
    """Convert a string to kebab-case."""
    s = re.sub(r"(\s|_|-)+", " ", s)
    s = re.sub(r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
               lambda mo: ' ' + mo.group(0).lower(), s)
    s = '-'.join(s.split())
    return s


def header_case(s: str) -> str:
    """Convert a string to Header-Case."""
    s = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1 \2', s)
    s = re.sub(r'[_\W]+', ' ', s)
    words = s.split()
    capitalized_words = [word.capitalize() for word in words]
    return '-'.join(capitalized_words)
