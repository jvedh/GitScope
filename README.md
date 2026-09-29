# GitScope

GitScope is a small GitHub repository analyzer. Paste a public GitHub repository URL (or `owner/repo`) to see its star and fork counts, issue count, languages, top contributors, recent commits, repository details, and root directory.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>. API docs are available at <http://127.0.0.1:8000/docs>.

### Run with Docker

```bash
docker build -t gitscope .
docker run --rm -p 8000:8000 -e GITHUB_TOKEN=your_token gitscope
```

Omit `-e GITHUB_TOKEN=...` to run without a token.

### Optional GitHub token

Unauthenticated GitHub API requests have a low hourly rate limit. Set a personal access token in the environment to raise it; the token is only read by the server and is never sent to the browser.

```bash
# macOS / Linux
export GITHUB_TOKEN=your_token
# Windows PowerShell
$env:GITHUB_TOKEN="your_token"
```

Use a fine-grained token with public repository read access only. Do not commit the token.

## Tests

```bash
pip install pytest
pytest
```

## What the analyzer reports

- Repository metadata and activity timestamps from GitHub's REST API
- Language byte counts from GitHub's language endpoint
- Up to 8 contributors, 10 recent commits, and 12 root-directory entries

Those list endpoints are intentionally bounded to keep requests quick. The commit view is a recent sample, not a lifetime commit count. GitHub may return partial language results for very large repositories, and private repositories are not supported by default.

## Stack

Python, FastAPI, httpx, GitHub REST API, HTML, CSS, and vanilla JavaScript.
