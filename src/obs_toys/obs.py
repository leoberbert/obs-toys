from __future__ import annotations

from pathlib import Path

from .models import PluginRecipe, PluginStatus


OBS_FLATPAK_APP_ID = "com.obsproject.Studio"


def obs_flatpak_root() -> Path:
    return Path.home() / ".var" / "app" / OBS_FLATPAK_APP_ID


def obs_plugin_root() -> Path:
    return obs_flatpak_root() / "config" / "obs-studio" / "plugins"


def is_obs_flatpak_installed() -> bool:
    return obs_flatpak_root().exists()


def plugin_status(recipe: PluginRecipe) -> PluginStatus:
    path = obs_plugin_root() / recipe.plugin_dir
    installed = path.exists()
    if installed:
        details = f"Installed at {path}"
    else:
        details = "Not installed in the OBS Flatpak profile."
    return PluginStatus(installed=installed, plugin_path=path, details=details)
