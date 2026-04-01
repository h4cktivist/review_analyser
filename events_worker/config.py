import os
from pathlib import Path


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_worker_env() -> None:
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent

    # Priority: real environment > events_worker/.env > project .env
    _load_env_file(current_dir / ".env")
    _load_env_file(root_dir / ".env")
