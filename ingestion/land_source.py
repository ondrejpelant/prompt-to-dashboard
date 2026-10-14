"""Land a registered source into the immutable landing zone.

The landing zone keeps source files exactly as they were delivered. Every run that
brings new content creates exactly one folder:

    data/landing/<source>/load_id=<UTC timestamp>/
        <source files, read-only>
        _manifest.json

Guarantees:
- integrity: the downloaded archive must match the sha256 pinned in sources.yml
- immutability: landed files are made read-only and never overwritten
- idempotency: content that has already landed is skipped (--force lands it again)
- atomicity: files are extracted into a temporary folder and moved into place only
  after every check passes, so a failed run never leaves a half-written load

Usage:
    python -m ingestion.land_source contoso_100k [--force] [--landing-root PATH]
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import py7zr
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "ingestion" / "sources.yml"
DEFAULT_LANDING_ROOT = REPO_ROOT / "data" / "landing"
MANIFEST_NAME = "_manifest.json"
CHUNK_SIZE = 1024 * 1024
USER_AGENT = "prompt-to-dashboard-ingestion/0.1"

log = logging.getLogger("land_source")


class LandingError(RuntimeError):
    """Raised when a source cannot be landed safely."""


@dataclass(frozen=True)
class Source:
    name: str
    description: str
    url: str
    sha256: str
    archive: str
    format: str
    license: str
    expected_files: tuple[str, ...]

    @classmethod
    def load(cls, name: str, sources_file: Path = SOURCES_FILE) -> "Source":
        registry = yaml.safe_load(sources_file.read_text(encoding="utf-8"))["sources"]
        if name not in registry:
            known = ", ".join(sorted(registry))
            raise LandingError(f"Unknown source '{name}'. Registered sources: {known}")
        entry = registry[name]
        return cls(
            name=name,
            description=" ".join(entry["description"].split()),
            url=entry["url"],
            sha256=entry["sha256"].lower(),
            archive=entry["archive"],
            format=entry["format"],
            license=entry["license"],
            expected_files=tuple(entry["expected_files"]),
        )


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def find_existing_load(source_dir: Path, archive_sha256: str) -> str | None:
    """Return the load_id of an earlier load of the same archive, if there is one."""
    for manifest_path in sorted(source_dir.glob(f"load_id=*/{MANIFEST_NAME}")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["archive"]["sha256"] == archive_sha256:
            return manifest["load_id"]
    return None


def download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out, CHUNK_SIZE)


def check_member_names(names: list[str]) -> None:
    """Refuse archives whose members would be written outside the target folder."""
    for name in names:
        parts = PurePosixPath(name.replace("\\", "/")).parts
        if name.startswith(("/", "\\")) or ".." in parts or (parts and ":" in parts[0]):
            raise LandingError(f"Unsafe path inside archive: {name!r}")


def extract(archive_path: Path, archive_format: str, target: Path) -> None:
    if archive_format == "7z":
        with py7zr.SevenZipFile(archive_path, mode="r") as archive:
            check_member_names(archive.getnames())
            archive.extractall(path=target)
    elif archive_format == "zip":
        with zipfile.ZipFile(archive_path) as archive:
            check_member_names(archive.namelist())
            archive.extractall(path=target)
    else:
        raise LandingError(f"Unsupported archive format: {archive_format!r}")


def describe_csv(path: Path) -> dict:
    """Header and record count, read with a real CSV parser (quoted newlines are safe)."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        columns = next(reader, [])
        records = sum(1 for _ in reader)
    return {"columns": columns, "records": records}


def describe_files(folder: Path, file_format: str) -> list[dict]:
    files = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        entry = {
            "name": path.relative_to(folder).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_of(path),
        }
        if file_format == "csv" and path.suffix.lower() == ".csv":
            entry |= describe_csv(path)
        files.append(entry)
    return files


def make_read_only(folder: Path) -> None:
    read_only = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    for path in folder.rglob("*"):
        if path.is_file():
            path.chmod(read_only)


def land(source: Source, landing_root: Path, force: bool = False) -> Path | None:
    """Land `source` and return the new load folder, or None if it was already landed."""
    source_dir = landing_root / source.name
    source_dir.mkdir(parents=True, exist_ok=True)

    existing = find_existing_load(source_dir, source.sha256)
    if existing and not force:
        log.info(
            "%s: archive %s already landed in load_id=%s; skipping (use --force to land again)",
            source.name,
            source.sha256[:12],
            existing,
        )
        return None

    load_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    final_dir = source_dir / f"load_id={load_id}"
    if final_dir.exists():
        raise LandingError(f"{final_dir} already exists; retry in a second")

    with tempfile.TemporaryDirectory(prefix=f".tmp-{load_id}-", dir=source_dir) as tmp:
        tmp_dir = Path(tmp)
        archive_path = tmp_dir / f"archive.{source.archive}"
        files_dir = tmp_dir / "files"

        log.info("%s: downloading %s", source.name, source.url)
        download(source.url, archive_path)

        actual_sha256 = sha256_of(archive_path)
        if actual_sha256 != source.sha256:
            raise LandingError(
                f"{source.name}: checksum mismatch - expected {source.sha256}, got "
                f"{actual_sha256}. The publisher may have changed the file; review it "
                "and update the pinned sha256 in sources.yml deliberately."
            )

        extract(archive_path, source.archive, files_dir)
        files = describe_files(files_dir, source.format)

        landed_names = {f["name"] for f in files}
        missing = sorted(set(source.expected_files) - landed_names)
        if missing:
            raise LandingError(f"{source.name}: expected files missing from archive: {missing}")
        unexpected = sorted(landed_names - set(source.expected_files))
        if unexpected:
            log.warning("%s: archive contains unexpected files: %s", source.name, unexpected)

        manifest = {
            "source": source.name,
            "description": source.description,
            "load_id": load_id,
            "landed_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "url": source.url,
            "license": source.license,
            "archive": {
                "format": source.archive,
                "bytes": archive_path.stat().st_size,
                "sha256": actual_sha256,
            },
            "files": files,
            "unexpected_files": unexpected,
        }
        (files_dir / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        make_read_only(files_dir)
        files_dir.rename(final_dir)

    total_records = sum(f.get("records", 0) for f in files)
    log.info(
        "%s: landed %d files (%s records) in %s",
        source.name,
        len(files),
        f"{total_records:,}",
        display_path(final_dir),
    )
    return final_dir


def display_path(path: Path) -> str:
    """Repo-relative path for readable logs, absolute when outside the repo."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Land a registered source into the landing zone.")
    parser.add_argument("source", help="source name from ingestion/sources.yml")
    parser.add_argument("--force", action="store_true", help="land again even if already landed")
    parser.add_argument(
        "--landing-root",
        type=Path,
        default=Path(os.environ.get("LANDING_ROOT", DEFAULT_LANDING_ROOT)),
        help="landing zone root folder (default: data/landing, or $LANDING_ROOT)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stdout)
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        land(Source.load(args.source), args.landing_root, force=args.force)
    except LandingError as exc:
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
