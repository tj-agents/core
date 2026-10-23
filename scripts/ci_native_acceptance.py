from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys
import tarfile
import urllib.request
import zipfile

import native_host_acceptance


CODEX_VERSION = "0.163.0-alpha.1"
CLAUDE_VERSION = "2.1.282"
ROOT = Path(__file__).resolve().parents[1]


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "tj-agents-native-acceptance"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def verify_digest(payload, expected, separator):
    if not isinstance(expected, str):
        raise ValueError("native release has no supported integrity digest")
    algorithm, delimiter, digest = expected.partition(separator)
    if not delimiter or algorithm not in {"sha256", "sha512"}:
        raise ValueError("native release has no supported integrity digest")
    actual = hashlib.new(algorithm, payload)
    encoded = actual.hexdigest() if separator == ":" else base64.b64encode(actual.digest()).decode("ascii")
    if encoded != digest:
        raise ValueError("native release integrity does not match metadata")


def archive_member(payload, member, archive_format):
    buffer = io.BytesIO(payload)
    if archive_format == "zip":
        with zipfile.ZipFile(buffer) as archive:
            matches = [item for item in archive.infolist() if item.filename == member and not item.is_dir()]
            if len(matches) != 1:
                raise ValueError(f"native archive must contain exactly one {member}")
            return archive.read(matches[0])
    with tarfile.open(fileobj=buffer, mode="r:gz") as archive:
        matches = [item for item in archive.getmembers() if item.name == member and item.isfile()]
        if len(matches) != 1:
            raise ValueError(f"native archive must contain exactly one regular {member}")
        with archive.extractfile(matches[0]) as executable:
            return executable.read()


def platform_assets(system, machine):
    if machine.lower() not in {"amd64", "x86_64"}:
        raise ValueError(f"native CI acceptance requires x64, found {machine}")
    if system == "Windows":
        return "x86_64-pc-windows-msvc.exe", "zip", "win32", ".exe", b"MZ"
    if system == "Linux":
        return "x86_64-unknown-linux-musl", "tar.gz", "linux", "", b"\x7fELF"
    raise ValueError(f"native CI acceptance does not support {system}")


def write_executable(path, payload, magic):
    if len(payload) <= 4096 or not payload.startswith(magic):
        raise ValueError(f"{path.name} is not the required native executable")
    path.write_bytes(payload)
    path.chmod(0o755)
    return path


def provision(directory, system, machine):
    target, archive_format, npm_platform, suffix, magic = platform_assets(system, machine)
    directory.mkdir(parents=True, exist_ok=True)
    release = json.loads(download(f"https://api.github.com/repos/openai/codex/releases/tags/rust-v{CODEX_VERSION}"))
    asset_name = f"codex-{target}.{archive_format}"
    assets = [asset for asset in release.get("assets", []) if asset.get("name") == asset_name]
    if len(assets) != 1:
        raise ValueError(f"Codex release must contain exactly one {asset_name}")
    asset = assets[0]
    payload = download(asset["browser_download_url"])
    verify_digest(payload, asset.get("digest", ""), ":")
    codex = write_executable(
        directory / f"codex{suffix}", archive_member(payload, f"codex-{target}", archive_format), magic,
    )
    package = f"@anthropic-ai/claude-code-{npm_platform}-x64"
    metadata = json.loads(download(f"https://registry.npmjs.org/{package}/{CLAUDE_VERSION}"))
    if metadata.get("name") != package or metadata.get("version") != CLAUDE_VERSION:
        raise ValueError("Claude package identity does not match its pinned version")
    distribution = metadata["dist"]
    payload = download(distribution["tarball"])
    verify_digest(payload, distribution.get("integrity", ""), "-")
    claude = write_executable(
        directory / f"claude{suffix}", archive_member(payload, f"package/claude{suffix}", "tar.gz"), magic,
    )
    return codex, claude


def main():
    if sys.version_info < (3, 11):
        raise SystemExit("native CI acceptance requires Python 3.11 or later")
    temporary = os.environ.get("RUNNER_TEMP")
    if not temporary or not Path(temporary).is_absolute():
        raise SystemExit("native CI acceptance requires an absolute RUNNER_TEMP")
    directory = Path(temporary) / "tj-agents-native-acceptance"
    artifacts = directory / "artifacts"
    try:
        codex, claude = provision(directory / "tools", platform.system(), platform.machine())
    except (OSError, ValueError, KeyError, tarfile.TarError, zipfile.BadZipFile) as error:
        native_host_acceptance.snapshot_diagnostic(artifacts, "provision.failure.log", f"{error}\n")
        print(f"native-host-provision: {error}", file=sys.stderr)
        return 1
    return native_host_acceptance.main([
        "--root", str(ROOT), "--marketplace", str(ROOT), "--codex", str(codex),
        "--claude", str(claude), "--artifacts", str(artifacts),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
