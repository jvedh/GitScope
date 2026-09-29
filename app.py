"""GitScope: a small GitHub repository analytics dashboard."""

import os
import re
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from github_client import GitHubClient, parse_repository_url

ROOT = Path(__file__).parent
app = FastAPI(title="GitScope", version="1.0.0", description="A lightweight GitHub repository analyzer")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/analyze")
async def analyze(repo: str = Query(..., min_length=1, max_length=300)) -> dict[str, Any]:
    try:
        owner, name = parse_repository_url(repo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(
            base_url="https://api.github.com", headers=headers, timeout=15.0, follow_redirects=True
        ) as http:
            client = GitHubClient(http)
            return await client.analyze(owner, name)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="GitHub took too long to respond. Try again.") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not reach GitHub. Check your connection and retry.") from exc
    except GitHubClient.APIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

