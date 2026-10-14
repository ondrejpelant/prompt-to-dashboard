"""Small cross-platform helpers used by the developer tasks in pyproject.toml."""

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def ensure_env() -> None:
    """Create .env from .env.example on the first run; never overwrite an existing one."""
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        print(".env already exists - leaving it unchanged.")
        return
    shutil.copyfile(REPO_ROOT / ".env.example", env_file)
    print("Created .env from .env.example - change the passwords in it before sharing anything.")
