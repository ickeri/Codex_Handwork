import json
import shutil
from pathlib import Path

from PySide6.QtCore import QStandardPaths

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_SETTINGS_FILE = PROJECT_ROOT / "settings.json"
SETTINGS_EXAMPLE_FILE = PROJECT_ROOT / "settings_example.json"
APP_NAME = "Codex_Handwork"


def _app_data_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.GenericDataLocation)
    if location:
        return Path(location) / APP_NAME
    return Path.home() / ".codex_handwork"


def _app_config_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.GenericConfigLocation)
    if location:
        return Path(location) / APP_NAME
    return _app_data_dir()


def get_settings_file() -> Path:
    return _app_config_dir() / "settings.json"


def get_counter_data_dir() -> Path:
    return _app_data_dir() / "data"


def ensure_settings_file() -> None:
    settings_file = get_settings_file()
    if settings_file.exists():
        return
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_EXAMPLE_FILE.exists():
        raise FileNotFoundError("缺少 settings.json，且未找到 settings_example.json")
    shutil.copyfile(SETTINGS_EXAMPLE_FILE, settings_file)


def load_settings() -> dict:
    ensure_settings_file()
    with get_settings_file().open("r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(data: dict) -> None:
    ensure_settings_file()
    with get_settings_file().open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_settings() -> dict:
    settings = load_settings()
    settings.setdefault("gui", {})
    return settings


def _build_bearer_headers(base_address: str, authorization_suffix: str, base_headers: dict) -> dict:
    headers = dict(base_headers)
    normalized_address = (base_address or "").strip().rstrip("/")
    auth_suffix = (authorization_suffix or "").strip()
    headers["Authorization"] = f"Bearer {auth_suffix}" if auth_suffix else ""
    if normalized_address:
        referer_base = normalized_address if "://" in normalized_address else f"http://{normalized_address}"
        headers["Referer"] = f"{referer_base}/management.html"
    else:
        headers["Referer"] = ""
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
        "headers": _build_bearer_headers(
            oauth_settings.get("base_address", ""),
            oauth_settings.get("authorization_suffix", ""),
            oauth_settings.get("headers", {}),
        ),
        "auth_url_params": oauth_settings["auth_url_params"],
        "request_timeout_seconds": oauth_settings["request_timeout_seconds"],
    }


def get_auth_file_download_config() -> dict:
    settings = get_settings()
    oauth_settings = settings["oauth"]
    base_address = oauth_settings["base_address"].strip()
    download_path = (oauth_settings.get("auth_file_download_path") or "/v0/management/auth-files/download").strip()
    if not download_path.startswith("/"):
        download_path = f"/{download_path}"
    return {
        "download_url": f"http://{base_address}{download_path}",
        "headers": _build_bearer_headers(
            oauth_settings.get("base_address", ""),
            oauth_settings.get("authorization_suffix", ""),
            oauth_settings.get("headers", {}),
        ),
        "request_timeout_seconds": oauth_settings.get("request_timeout_seconds", 30),
    }


def get_project_token_dir() -> Path:
    settings = get_settings()
    folder_name = str(settings.get("oauth", {}).get("token_dir_name") or "token").strip() or "token"
    return PROJECT_ROOT / folder_name


def get_cpa_upload_request_config() -> dict:
    settings = get_settings()
    upload_settings = settings.get("cpa_upload") or {}
    host = (upload_settings.get("host") or "").strip()
    auth_suffix = (upload_settings.get("authorization_suffix") or "").strip()

    url = f"http://{host}/v0/management/auth-files" if host else ""
    origin = f"http://{host}" if host else ""
    referer = f"http://{host}/management.html" if host else ""

    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    if auth_suffix:
        headers["Authorization"] = f"Bearer {auth_suffix}"
    if origin:
        headers["Origin"] = origin
        headers["Referer"] = referer

    return {
        "url": url,
        "headers": headers,
        "request_timeout_seconds": upload_settings.get("request_timeout_seconds", 30),
    }
