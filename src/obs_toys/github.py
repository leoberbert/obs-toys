from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.request import Request, urlopen

from .models import AssetSource


USER_AGENT = "obs-toys/0.1 (+https://github.com/leoberbert/obs-toys)"


@dataclass(slots=True)
class GitHubAsset:
    name: str
    download_url: str


def _request_json(url: str) -> dict | list:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def _release_candidates(source: AssetSource) -> list[dict]:
    repo_url = f"https://api.github.com/repos/{source.repo}/releases"
    releases = _request_json(repo_url)
    assert isinstance(releases, list)
    if not source.prereleases:
        releases = [release for release in releases if not release.get("prerelease")]
    return releases


def resolve_asset(source: AssetSource) -> GitHubAsset:
    releases = _release_candidates(source)
    if not releases:
        raise RuntimeError(f"No releases found for {source.repo}")

    patterns = [re.compile(pattern) for pattern in source.asset_patterns]
    for release in releases:
        for asset in release.get("assets", []):
            asset_name = asset["name"]
            if any(pattern.search(asset_name) for pattern in patterns):
                return GitHubAsset(name=asset_name, download_url=asset["browser_download_url"])

    raise RuntimeError(f"No matching release asset found for {source.repo}")
