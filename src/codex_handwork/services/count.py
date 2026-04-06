"""账号数量查询（本地/远端）"""

import requests

from codex_handwork.settings import get_cpa_upload_request_config, get_oauth_request_config, get_settings


def get_account_count() -> int:
    """根据配置获取本地或远端账号数量"""
    upload_enabled = get_settings().get("cpa_upload", {}).get("enabled", True)

    if upload_enabled:
        return _get_remote_account_count()
    else:
        return _get_local_account_count()


def _get_local_account_count() -> int:
    """从本地 CPA 获取账号数量"""
    config = get_oauth_request_config()
    base_url = config["auth_url"].rsplit("/", 1)[0]  # 去掉最后的路径部分
    files_url = f"{base_url}/auth-files"

    response = requests.get(
        files_url,
        headers=config["headers"],
        timeout=config["request_timeout_seconds"],
    )
    response.raise_for_status()
    data = response.json()
    files = data.get("files", [])
    return len(files)


def _get_remote_account_count() -> int:
    """从远端服务器获取账号数量"""
    config = get_cpa_upload_request_config()
    if not config["url"]:
        raise ValueError("远端服务器地址未配置")

    response = requests.get(
        config["url"],
        headers=config["headers"],
        timeout=config["request_timeout_seconds"],
    )
    response.raise_for_status()
    data = response.json()
    files = data.get("files", [])
    return len(files)

