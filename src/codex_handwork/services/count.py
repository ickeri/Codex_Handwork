import requests

from codex_handwork.settings import get_oauth_request_config


def get_auth_file_count() -> int:
    config = get_oauth_request_config()
    response = requests.get(
        config["count_url"],
        headers=config["headers"],
        timeout=config["request_timeout_seconds"],
    )
    response.raise_for_status()
    payload = response.json() or {}
    files = payload.get("files") or []
    if not isinstance(files, list):
        raise ValueError("files 字段不是列表")
    return len(files)


if __name__ == "__main__":
    print(get_auth_file_count())
