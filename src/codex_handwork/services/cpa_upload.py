from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import requests
from curl_cffi import requests as cffi_requests

from codex_handwork.settings import get_auth_file_download_config, get_cpa_upload_request_config, get_project_token_dir, get_settings


@dataclass(slots=True)
class TransferResult:
    success: bool
    message: str
    file_path: Path | None = None
    download_name: str = ""


def build_auth_file_name(email: str) -> str:
    normalized_email = (email or "").strip()
    if not normalized_email:
        raise ValueError("注册成功，但当前邮箱为空，无法推导 auth file name")
    return f"codex-{quote(normalized_email, safe='@')}-free.json"


def download_auth_file(name: str) -> Path:
    config = get_auth_file_download_config()
    if not config["download_url"]:
        raise ValueError("本地 auth 文件下载地址未配置")
    token_dir = get_project_token_dir()
    token_dir.mkdir(parents=True, exist_ok=True)
    target = token_dir / name.replace("%40", "@")
    response = cffi_requests.get(
        config["download_url"],
        params={"name": name},
        headers=config["headers"],
        impersonate="chrome",
        timeout=config["request_timeout_seconds"],
    )
    response.raise_for_status()
    target.write_bytes(response.content)
    return target


def upload_auth_file(file_path: str | Path) -> None:
    config = get_cpa_upload_request_config()
    upload_url = config["url"]
    if not upload_url:
        raise ValueError("远端上传地址未配置")
    auth_header = (config["headers"].get("Authorization") or "").strip()
    if not auth_header:
        raise ValueError("远端上传密码未配置")
    target = Path(file_path)
    with target.open("rb") as fh:
        response = requests.post(
            upload_url,
            headers=config["headers"],
            files={"file": (target.name, fh, "application/json")},
            timeout=config["request_timeout_seconds"],
        )
    response.raise_for_status()


def download_and_upload_auth_file(email: str) -> TransferResult:
    upload_enabled = get_settings().get("cpa_upload", {}).get("enabled", True)

    try:
        download_name = build_auth_file_name(email)
        file_path = download_auth_file(download_name)
    except Exception as exc:
        return TransferResult(False, f"下载失败：{exc}", download_name=locals().get("download_name", ""))

    if not upload_enabled:
        return TransferResult(True, "认证文件已下载（远端上传已禁用）", file_path=file_path, download_name=download_name)

    try:
        upload_auth_file(file_path)
    except Exception as exc:
        return TransferResult(False, f"下载成功，但上传失败：{exc}", file_path=file_path, download_name=download_name)
    return TransferResult(True, "认证文件已下载并上传成功", file_path=file_path, download_name=download_name)
