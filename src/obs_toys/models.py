from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AssetSource:
    asset_patterns: list[str]
    repo: str = ""
    provider: str = "github"
    resource_path: str = ""
    prereleases: bool = False


@dataclass(slots=True)
class InstallLayout:
    sources: list[str]
    destination: str
    kind: str = "file"
    optional: bool = False


@dataclass(slots=True)
class PluginRecipe:
    plugin_id: str
    name: str
    summary: str
    description: str
    project_url: str
    source: AssetSource
    plugin_dir: str
    layouts: list[InstallLayout]
    supported_formats: list[str]


@dataclass(slots=True)
class PluginStatus:
    installed: bool
    plugin_path: Path
    details: str


@dataclass(slots=True)
class InstallResult:
    success: bool
    plugin_id: str
    message: str
