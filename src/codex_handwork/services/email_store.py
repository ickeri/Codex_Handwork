import json
from datetime import datetime
from pathlib import Path

from codex_handwork.settings import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
COUNTER_FILE = DATA_DIR / "email_counter.json"
LEGACY_COUNTER_FILE = PROJECT_ROOT / "email_counter.json"


def _email_settings() -> dict:
    return get_settings()["email"]


def _default_counter() -> dict:
    return {"last_index": 0, "last_email": "", "updated_at": ""}


def _read_counter_file(path: Path) -> dict:
    settings = _email_settings()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("email_counter.json 格式错误")

    last_index = int(data.get("last_index", 0))
    if last_index < 0 or last_index > settings["max_index"]:
        raise ValueError("email_counter.json 中 last_index 超出范围")

    return {
        "last_index": last_index,
        "last_email": str(data.get("last_email", "")),
        "updated_at": str(data.get("updated_at", "")),
    }


def load_counter() -> dict:
    if COUNTER_FILE.exists():
        return _read_counter_file(COUNTER_FILE)
    if LEGACY_COUNTER_FILE.exists():
        return _read_counter_file(LEGACY_COUNTER_FILE)
    return _default_counter()


def format_email(index: int) -> str:
    settings = _email_settings()
    if index < settings["min_index"] or index > settings["max_index"]:
        raise ValueError("邮箱编号超出范围")
    return f"{settings['prefix']}{index:05d}{settings['domain']}"


def save_counter(index: int) -> dict:
    email = format_email(index)
    payload = {
        "last_index": index,
        "last_email": email,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with COUNTER_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def allocate_next_email() -> str:
    settings = _email_settings()
    counter = load_counter()
    next_index = counter["last_index"] + 1
    if next_index > settings["max_index"]:
        raise RuntimeError("邮箱编号已用尽")
    save_counter(next_index)
    return format_email(next_index)
