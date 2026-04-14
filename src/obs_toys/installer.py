from __future__ import annotations

import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

from .github import resolve_asset
from .models import InstallResult, PluginRecipe
from .obs import obs_plugin_root


def _download(url: str, target: Path) -> None:
    request = Request(url, headers={"User-Agent": "obs-toys/0.1"})
    with urlopen(request) as response, target.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def _ensure_supported_archive(asset_name: str, supported_formats: list[str]) -> None:
    if not any(asset_name.endswith(suffix) for suffix in supported_formats):
        raise RuntimeError(f"Unsupported asset format: {asset_name}")


def _extract_tar(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination)


def _extract_zip(archive_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(destination)


def _extract_deb(archive_path: Path, destination: Path) -> None:
    if shutil.which("dpkg-deb"):
        subprocess.run(["dpkg-deb", "-x", str(archive_path), str(destination)], check=True)
        return

    if not shutil.which("ar"):
        raise RuntimeError("Installing .deb assets requires either dpkg-deb or ar to be available.")

    ar_extract_dir = destination / "_deb"
    ar_extract_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ar", "x", str(archive_path)], cwd=ar_extract_dir, check=True)

    data_member = next(iter(sorted(ar_extract_dir.glob("data.tar.*"))), None)
    if data_member is None:
        raise RuntimeError("Could not locate data.tar.* inside the .deb archive.")

    _extract_tar(data_member, destination)


def _extract_archive(archive_path: Path, destination: Path) -> None:
    name = archive_path.name
    if name.endswith((".tar.gz", ".tar.xz", ".tar.bz2", ".tgz")):
        _extract_tar(archive_path, destination)
        return
    if name.endswith(".zip"):
        _extract_zip(archive_path, destination)
        return
    if name.endswith(".deb"):
        _extract_deb(archive_path, destination)
        return
    raise RuntimeError(f"Unsupported archive type: {name}")


def _is_supported_archive(path: Path) -> bool:
    return path.name.endswith((".tar.gz", ".tar.xz", ".tar.bz2", ".tgz", ".zip", ".deb"))


def _extract_nested_archives(extracted_root: Path) -> None:
    pending = [path for path in extracted_root.rglob("*") if path.is_file() and _is_supported_archive(path)]
    seen: set[Path] = set()

    while pending:
        archive_path = pending.pop(0)
        if archive_path in seen or not archive_path.exists():
            continue
        seen.add(archive_path)

        nested_dir = archive_path.parent / f"{archive_path.name}.contents"
        nested_dir.mkdir(parents=True, exist_ok=True)
        _extract_archive(archive_path, nested_dir)

        for candidate in nested_dir.rglob("*"):
            if candidate.is_file() and _is_supported_archive(candidate) and candidate not in seen:
                pending.append(candidate)


def _resolve_source_path(extracted_root: Path, layout_sources: list[str]) -> Path:
    for source in layout_sources:
        candidate = extracted_root / source
        if candidate.exists():
            return candidate

    for source in layout_sources:
        normalized = source.strip("/").replace("\\", "/")
        for candidate in extracted_root.rglob("*"):
            if not candidate.exists():
                continue
            candidate_path = candidate.as_posix()
            if candidate_path.endswith(normalized):
                return candidate

    joined = ", ".join(layout_sources)
    raise RuntimeError(f"Expected path not found in archive. Checked: {joined}")


def _copy_layouts(recipe: PluginRecipe, extracted_root: Path) -> Path:
    target_root = obs_plugin_root() / recipe.plugin_dir
    target_root.mkdir(parents=True, exist_ok=True)

    for layout in recipe.layouts:
        source_path = _resolve_source_path(extracted_root, layout.sources)
        destination_path = target_root / layout.destination
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.is_dir() or layout.kind == "dir":
            if layout.destination in ("", "."):
                if target_root.exists():
                    shutil.rmtree(target_root)
                shutil.copytree(source_path, target_root)
                continue
            if destination_path.exists():
                shutil.rmtree(destination_path)
            shutil.copytree(source_path, destination_path)
        else:
            shutil.copy2(source_path, destination_path)

    return target_root


def install_plugin(recipe: PluginRecipe) -> InstallResult:
    try:
        asset = resolve_asset(recipe.source)
        _ensure_supported_archive(asset.name, recipe.supported_formats)

        with tempfile.TemporaryDirectory(prefix=f"obs-toys-{recipe.plugin_id}-") as temp_dir:
            temp_root = Path(temp_dir)
            archive_path = temp_root / asset.name
            extracted_root = temp_root / "extracted"
            extracted_root.mkdir(parents=True, exist_ok=True)

            _download(asset.download_url, archive_path)
            _extract_archive(archive_path, extracted_root)
            _extract_nested_archives(extracted_root)
            plugin_root = _copy_layouts(recipe, extracted_root)

        return InstallResult(
            success=True,
            plugin_id=recipe.plugin_id,
            message=f"{recipe.name} installed into {plugin_root}",
        )
    except Exception as exc:
        return InstallResult(success=False, plugin_id=recipe.plugin_id, message=str(exc))


def remove_plugin(recipe: PluginRecipe) -> InstallResult:
    plugin_root = obs_plugin_root() / recipe.plugin_dir
    try:
        if not plugin_root.exists():
            return InstallResult(
                success=True,
                plugin_id=recipe.plugin_id,
                message=f"{recipe.name} is already absent from {plugin_root}",
            )

        shutil.rmtree(plugin_root)
        return InstallResult(
            success=True,
            plugin_id=recipe.plugin_id,
            message=f"{recipe.name} removed from {plugin_root}",
        )
    except Exception as exc:
        return InstallResult(success=False, plugin_id=recipe.plugin_id, message=str(exc))
