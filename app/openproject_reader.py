"""Read-only OpenProject API v3 adapter. No direct database access."""
import os
from urllib.parse import urlparse
import httpx


def _configuration():
    base = os.environ.get("OPENPROJECT_URL", "").rstrip("/")
    token = os.environ.get("OPENPROJECT_API_TOKEN", "")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("OPENPROJECT_URL must be an HTTPS origin")
    if parsed.path not in ("", "/"):
        raise ValueError("OPENPROJECT_URL must not contain a path")
    if not token:
        raise ValueError("OPENPROJECT_API_TOKEN required")
    return base, token


def read_work_packages(project_id: int, *, max_pages: int = 5, page_size: int = 100, client=None):
    """Fetch bounded project work packages; never follow arbitrary server-provided URLs."""
    if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0:
        raise ValueError("invalid project id")
    if not 1 <= max_pages <= 20 or not 1 <= page_size <= 100:
        raise ValueError("invalid paging limits")
    base, token = _configuration()
    result = []
    owned = client is None
    http = client or httpx.Client(timeout=15.0, follow_redirects=False)
    try:
        for page in range(1, max_pages + 1):
            response = http.get(
                f"{base}/api/v3/projects/{project_id}/work_packages",
                params={"pageSize": page_size, "offset": page},
                auth=("apikey", token),
                headers={"Accept": "application/hal+json"},
            )
            response.raise_for_status()
            body = response.json()
            elements = body.get("_embedded", {}).get("elements")
            if not isinstance(elements, list):
                raise ValueError("invalid OpenProject collection response")
            result.extend(elements)
            total = body.get("total")
            if isinstance(total, int) and len(result) >= total:
                break
            if len(elements) < page_size:
                break
        return {"project_id": project_id, "work_packages": result, "count": len(result),
                "bounded": len(result) >= max_pages * page_size}
    finally:
        if owned:
            http.close()
