import time

import requests

from codex_handwork.settings import get_oauth_request_config, get_settings


def get_auth_status(state: str) -> dict:
    config = get_oauth_request_config()
    response = requests.get(
        config["status_url"],
        headers=config["headers"],
        params={"state": state},
        timeout=config["request_timeout_seconds"],
    )
    response.raise_for_status()
    return response.json()


def wait_for_auth_ok(state: str, interval: int | None = None) -> dict:
    if interval is None:
        interval = max(get_settings()["gui"]["auth_poll_interval_ms"] / 1000, 0.1)
    while True:
        data = get_auth_status(state)
        status = data.get("status")
        print(data)
        if status == "ok":
            return data
        if status != "wait":
            raise RuntimeError(f"unexpected status: {status}")
        time.sleep(interval)


if __name__ == "__main__":
    result = wait_for_auth_ok("af29b2630d8f6a03a2e493250b6b1bad")
    print(result)
