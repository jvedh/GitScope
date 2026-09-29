import pytest

from github_client import parse_repository_url


@pytest.mark.parametrize("value, expected", [
    ("octocat/Hello-World", ("octocat", "Hello-World")),
    ("https://github.com/fastapi/fastapi", ("fastapi", "fastapi")),
    ("https://github.com/fastapi/fastapi.git/", ("fastapi", "fastapi")),
    ("git@github.com:pallets/flask.git", ("pallets", "flask")),
])
def test_parse_repository_url(value, expected):
    assert parse_repository_url(value) == expected


@pytest.mark.parametrize("value", [
    "https://gitlab.com/owner/repo",
    "owner",
    "owner/repo/extra",
    "https://github.com/owner",
    "https://github.com/owner/repo/issues",
])
def test_rejects_invalid_repository_urls(value):
    with pytest.raises(ValueError):
        parse_repository_url(value)
