# OBS Toys

<p align="center">
  <img src="src/obs_toys/data/icons/obs-toys.svg" alt="OBS Toys Logo" width="128" height="128">
</p>

<p align="center">
  <strong>A friendly app for installing OBS plugins on Linux.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-green.svg" alt="License"></a>
  <a href="https://www.gtk.org/"><img src="https://img.shields.io/badge/GTK-4.0+-orange.svg" alt="GTK"></a>
  <a href="https://gnome.pages.gitlab.gnome.org/libadwaita/"><img src="https://img.shields.io/badge/libadwaita-1.0+-purple.svg" alt="libadwaita"></a>
  <a href="https://github.com/leoberbert/obs-toys"><img src="https://img.shields.io/badge/GitHub-obs--toys-black.svg" alt="GitHub"></a>
</p>

**OBS Toys** is a desktop app focused on making OBS Studio plugins easier to use on Linux. Instead of manually unpacking `.deb`, `.zip`, or `.tar.*` files and copying plugin assets into the correct OBS profile directories, OBS Toys handles that workflow in a cleaner GTK interface.

## Why OBS Toys

- **Built for OBS on Linux**: install plugins into `~/.config/obs-studio/plugins` without manual extraction steps.
- **Curated plugin catalog**: only plugins that make sense for this workflow should appear in the app.
- **Simple install and removal flow**: confirm, install, remove, and verify status in a straightforward UI.
- **Linux-native desktop experience**: GTK4 + libadwaita with a layout aligned to the Linux Toys ecosystem.
- **Multiple plugin sources**: supports both GitHub Releases and OBS Resources.

## Current Plugin Support

- `OBS Multi RTMP`
- `Aitum Stream Suite`
- `OBS Move Transition`
- `OBS Advanced Masks`
- `OBS Stroke Glow Shadow`
- `OBS Retro Effects`
- `OBS 3D Effect`
- `Composite Blur`
- `Source Clone`
- `Advanced Scene Switcher`

## What OBS Toys Does

- Detects whether OBS is installed on the system
- Shows a searchable plugin catalog
- Downloads release assets from GitHub and OBS Resources
- Extracts `.deb`, `.zip`, and `.tar.*` archives
- Copies plugin files into the correct OBS plugin directory
- Detects when a plugin is already installed
- Allows removing installed plugins from the same interface

## Run Locally

```bash
cd /home/leoberbert/github/leoberbert/obs-toys
PYTHONPATH=src python3 -m obs_toys
```

Editable install:

```bash
cd /home/leoberbert/github/leoberbert/obs-toys
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
obs-toys
```

## Project Structure

- `src/obs_toys/ui.py`: GTK/libadwaita interface
- `src/obs_toys/catalog.py`: curated recipe loader
- `src/obs_toys/github.py`: GitHub Releases and OBS Resources asset resolver
- `src/obs_toys/installer.py`: download, extraction, and install logic
- `src/obs_toys/obs.py`: OBS path and installation status helpers
- `src/obs_toys/data/plugins.json`: plugin catalog
- `src/obs_toys/data/icons/`: project icons and UI assets

## Notes

- OBS Toys is intentionally curated. Not every OBS plugin published for Linux is guaranteed to work correctly out of the box.
- Some plugins come from GitHub Releases, while others are better discovered through OBS Resources.
- The goal is to keep the list practical and reliable rather than simply large.

## Roadmap

- Add more validated OBS plugins
- Improve metadata and compatibility checks per plugin
- Add app icon integration for system installation
- Add package/install assets for broader distribution

## License

This project is licensed under the **GPL-3.0-or-later** license.
