from __future__ import annotations

import json
from importlib import resources

from .models import AssetSource, InstallLayout, PluginRecipe


def load_catalog() -> list[PluginRecipe]:
    raw_catalog = resources.files("obs_toys").joinpath("data/plugins.json").read_text(encoding="utf-8")
    data = json.loads(raw_catalog)

    recipes: list[PluginRecipe] = []
    for entry in data["plugins"]:
        recipes.append(
            PluginRecipe(
                plugin_id=entry["id"],
                name=entry["name"],
                summary=entry["summary"],
                description=entry["description"],
                project_url=entry["project_url"],
                source=AssetSource(
                    repo=entry["source"].get("repo", ""),
                    asset_patterns=entry["source"]["asset_patterns"],
                    provider=entry["source"].get("provider", "github"),
                    resource_path=entry["source"].get("resource_path", ""),
                    prereleases=entry["source"].get("prereleases", False),
                ),
                plugin_dir=entry["install"]["plugin_dir"],
                layouts=[
                    InstallLayout(
                        sources=layout["from"] if isinstance(layout["from"], list) else [layout["from"]],
                        destination=layout["to"],
                        kind=layout.get("kind", "file"),
                        optional=layout.get("optional", False),
                    )
                    for layout in entry["install"]["layouts"]
                ],
                supported_formats=entry["supported_formats"],
            )
        )
    return recipes
