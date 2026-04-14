from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .models import AssetSource


USER_AGENT = "obs-toys/0.1 (+https://github.com/leoberbert/obs-toys)"
OBS_RESOURCES_BASE = "https://obsproject.com/forum/resources/"


@dataclass(slots=True)
class ResolvedAsset:
    name: str
    download_url: str


@dataclass(slots=True)
class _ObsResourceLink:
    href: str
    text: str


class _ObsResourceHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[_ObsResourceLink] = []
        self.texts: list[str] = []
        self.events: list[tuple[str, object]] = []
        self._current_href: str | None = None
        self._current_link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            attr_map = dict(attrs)
            self._current_href = attr_map.get("href")
            self._current_link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current_href:
            text = " ".join(part.strip() for part in self._current_link_text if part.strip()).strip()
            link = _ObsResourceLink(href=self._current_href, text=text)
            self.links.append(link)
            self.events.append(("link", link))
            self._current_href = None
            self._current_link_text = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        self.texts.append(text)
        self.events.append(("text", text))
        if self._current_href is not None:
            self._current_link_text.append(text)


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


def _request_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request) as response:
        return response.read().decode("utf-8", errors="replace")


def _resolve_github_asset(source: AssetSource) -> ResolvedAsset:
    releases = _release_candidates(source)
    if not releases:
        raise RuntimeError(f"No releases found for {source.repo}")

    patterns = [re.compile(pattern) for pattern in source.asset_patterns]
    for release in releases:
        for asset in release.get("assets", []):
            asset_name = asset["name"]
            if any(pattern.search(asset_name) for pattern in patterns):
                return ResolvedAsset(name=asset_name, download_url=asset["browser_download_url"])

    raise RuntimeError(f"No matching release asset found for {source.repo}")


def _resolve_obs_resource_asset(source: AssetSource) -> ResolvedAsset:
    if not source.resource_path:
        raise RuntimeError("OBS Resources source is missing resource_path")

    download_page_url = urljoin(OBS_RESOURCES_BASE, source.resource_path)
    html = _request_text(download_page_url)
    patterns = [re.compile(pattern) for pattern in source.asset_patterns]
    parser = _ObsResourceHTMLParser()
    parser.feed(html)

    for index, (kind, payload) in enumerate(parser.events):
        if kind != "text":
            continue
        asset_name = str(payload).strip()
        if not any(pattern.search(asset_name) for pattern in patterns):
            continue

        for offset in range(1, 8):
            for neighbor_index in (index - offset, index + offset):
                if neighbor_index < 0 or neighbor_index >= len(parser.events):
                    continue
                neighbor_kind, neighbor_payload = parser.events[neighbor_index]
                if neighbor_kind != "link":
                    continue
                link = neighbor_payload
                assert isinstance(link, _ObsResourceLink)
                if "download?file=" not in link.href:
                    continue
                if link.text.lower() != "download":
                    continue
                return ResolvedAsset(
                    name=asset_name,
                    download_url=urljoin(download_page_url, link.href),
                )

    raise RuntimeError(f"No matching OBS Resources asset found at {download_page_url}")


def resolve_asset(source: AssetSource) -> ResolvedAsset:
    if source.provider == "obs_resources":
        return _resolve_obs_resource_asset(source)
    return _resolve_github_asset(source)
