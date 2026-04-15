from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from .i18n import _
from .models import PluginRecipe, PluginStatus


OBS_CONFIG_DIR = Path.home() / ".config" / "obs-studio"
OBS_PLUGIN_DIR = OBS_CONFIG_DIR / "plugins"


def obs_plugin_root() -> Path:
    return OBS_PLUGIN_DIR


def is_obs_installed() -> bool:
    return OBS_CONFIG_DIR.exists() or shutil.which("obs") is not None or shutil.which("obs-studio") is not None


def is_obs_running() -> bool:
    for process_name in ("obs", "obs-studio"):
        result = subprocess.run(
            ["pgrep", "-x", process_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True
    return False


def close_obs(timeout_seconds: float = 5.0) -> bool:
    for process_name in ("obs", "obs-studio"):
        subprocess.run(["pkill", "-TERM", "-x", process_name], check=False)

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not is_obs_running():
            return True
        time.sleep(0.2)

    for process_name in ("obs", "obs-studio"):
        subprocess.run(["pkill", "-KILL", "-x", process_name], check=False)

    time.sleep(0.3)
    return not is_obs_running()


def obs_installation_label() -> str:
    return _("system OBS profile")


def plugin_status(recipe: PluginRecipe) -> PluginStatus:
    path = obs_plugin_root() / recipe.plugin_dir
    installed = path.exists()
    if installed:
        details = _("Installed at {path}", path=path)
    else:
        details = _("Not installed in the system OBS profile.")
    return PluginStatus(installed=installed, plugin_path=path, details=details)
