"""GitHub REST API access and response shaping for GitScope."""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

_REPO_PATH = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def parse_repository_url(value: str) -> tuple[str, str]:
    """Accept owner/repo, github.com URLs, and git@github.com remotes."""
    value = value.strip()
    if value.startswith("git@github.com:"):
        path = value.removeprefix("git@github.com:")
    elif "://" in value:
        parsed = urlparse(value)
        if parsed.hostname not in {"github.com", "www.github.com"}:
            raise ValueError("Enter a github.com repository URL or owner/repo.")
        path = parsed.path.strip("/")
    else:
        path = value.strip("/")

    path = path.removesuffix(".git").strip("/")
    parts = path.split("/")
    if len(parts) != 2 or not _REPO_PATH.fullmatch(path):
        raise ValueError("Use a repository URL like https://github.com/owner/repo or owner/repo.")
    return parts[0], parts[1]


class GitHubClient:
    class APIError(Exception):
        def __init__(self, status_code: int, message: str):
            self.status_code = status_code
            self.message = message
            super().__init__(message)

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def _get(self, path: str) -> Any:
        response = await self.client.get(path)
        if response.status_code == 404:
            raise self.APIError(404, "Repository not found, or it is private.")
        if response.status_code == 403:
            reset = response.headers.get("X-RateLimit-Reset")
            hint = "GitHub API rate limit reached. Add a GITHUB_TOKEN and retry."
            if reset and reset.isdigit():
                reset_at = datetime.fromtimestamp(int(reset), tz=timezone.utc).strftime("%H:%M UTC")
                hint = f"GitHub API rate limit reached. It resets around {reset_at}. Add a GITHUB_TOKEN to raise the limit."
            raise self.APIError(429, hint)
        if response.status_code >= 400:
            raise self.APIError(502, f"GitHub returned an error ({response.status_code}).")
        return response.json()

    async def analyze(self, owner: str, name: str) -> dict[str, Any]:
        root = f"/repos/{owner}/{name}"
        metadata = await self._get(root)

        async def optional(path: str, fallback: Any) -> Any:
            try:
                return await self._get(path)
            except self.APIError:
                return fallback

        languages, contributors, commits, contents = await asyncio.gather(
            optional(f"{root}/languages", {}),
            optional(f"{root}/contributors?per_page=8", []),
            optional(f"{root}/commits?per_page=20", []),
            optional(f"{root}/contents", []),
        )

        language_total = sum(languages.values()) or 1
        language_rows = [
            {"name": lang, "bytes": count, "percent": round(count * 100 / language_total, 1)}
            for lang, count in sorted(languages.items(), key=lambda pair: pair[1], reverse=True)
        ]
        contributor_rows = [
            {
                "login": item.get("login", "unknown"),
                "avatar_url": item.get("avatar_url", ""),
                "html_url": item.get("html_url", "#"),
                "contributions": item.get("contributions", 0),
            }
            for item in contributors[:8]
        ]
        commit_rows = []
        for item in commits[:10]:
            commit = item.get("commit", {})
            author = commit.get("author") or {}
            commit_rows.append({
                "sha": item.get("sha", "")[:7],
                "message": (commit.get("message", "").splitlines() or ["(no message)"])[0],
                "author": author.get("name", "Unknown"),
                "date": author.get("date"),
                "url": item.get("html_url", "#"),
            })
        files = [
            {"name": item.get("name", ""), "type": item.get("type", "file"), "size": item.get("size", 0), "url": item.get("html_url", "#")}
            for item in contents[:12]
        ] if isinstance(contents, list) else []

        return {
            "repository": {
                "name": metadata.get("full_name", f"{owner}/{name}"),
                "description": metadata.get("description") or "No repository description provided.",
                "url": metadata.get("html_url", f"https://github.com/{owner}/{name}"),
                "owner": metadata.get("owner", {}).get("login", owner),
                "owner_avatar": metadata.get("owner", {}).get("avatar_url", ""),
                "stars": metadata.get("stargazers_count", 0),
                "forks": metadata.get("forks_count", 0),
                "watchers": metadata.get("subscribers_count", metadata.get("watchers_count", 0)),
                "open_issues": metadata.get("open_issues_count", 0),
                "default_branch": metadata.get("default_branch", "main"),
                "license": (metadata.get("license") or {}).get("spdx_id", "Not specified"),
                "created_at": metadata.get("created_at"),
                "updated_at": metadata.get("updated_at"),
                "pushed_at": metadata.get("pushed_at"),
                "archived": metadata.get("archived", False),
                "topics": metadata.get("topics", []),
            },
            "languages": language_rows,
            "contributors": contributor_rows,
            "commits": commit_rows,
            "commit_sample_size": len(commits),
            "files": files,
        }
