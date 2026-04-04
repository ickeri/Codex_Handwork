import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = PROJECT_ROOT / "settings.json"
SETTINGS_EXAMPLE_FILE = PROJECT_ROOT / "settings_example.json"


def ensure_settings_file() -> None:
    if SETTINGS_FILE.exists():
        return
    if not SETTINGS_EXAMPLE_FILE.exists():
        raise FileNotFoundError("缺少 settings.json，且未找到 settings_example.json")
    shutil.copyfile(SETTINGS_EXAMPLE_FILE, SETTINGS_FILE)


def load_settings() -> dict:
    ensure_settings_file()
    with SETTINGS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(data: dict) -> None:
    ensure_settings_file()
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_settings() -> dict:
    return load_settings()


def _build_oauth_headers(oauth_settings: dict) -> dict:
    headers = dict(oauth_settings["headers"])
    base_address = oauth_settings["base_address"].strip()
    auth_suffix = oauth_settings["authorization_suffix"].strip()
    headers["Authorization"] = f"Bearer {auth_suffix}" if auth_suffix else ""
    headers["Referer"] = f"http://{base_address}/management.html" if base_address else ""
    return headers


def get_mail_request_config() -> dict:
    settings = get_settings()
    mail_settings = settings["mail"]
    headers = dict(mail_settings["headers"])
    headers["authorization"] = mail_settings["authorization"].strip()
    return {
        "url": mail_settings["url"],
        "params": mail_settings["params"],
        "headers": headers,
        "request_timeout_seconds": mail_settings["request_timeout_seconds"],
    }


def get_oauth_request_config() -> dict:
    settings = get_settings()
    oauth_settings = settings["oauth"]
    base_address = oauth_settings["base_address"].strip()
    return {
        "auth_url": f"http://{base_address}/v0/management/codex-auth-url",
        "status_url": f"http://{base_address}/v0/management/get-auth-status",
        "count_url": f"http://{base_address}/v0/management/auth-files",
        "headers": _build_oauth_headers(oauth_settings),
        "auth_url_params": oauth_settings["auth_url_params"],
        "request_timeout_seconds": oauth_settings["request_timeout_seconds"],
    }
