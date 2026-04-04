import requests

from codex_handwork.services.status import wait_for_auth_ok
from codex_handwork.settings import get_oauth_request_config


def get_auth_url() -> dict:
    config = get_oauth_request_config()
    response = requests.get(
        config["auth_url"],
        headers=config["headers"],
        params=config["auth_url_params"],
        timeout=config["request_timeout_seconds"],
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    auth_data = get_auth_url()
    state = auth_data.get("state")
    print({
        "state": state,
        "url": auth_data.get("url"),
    })
    if not state:
        raise RuntimeError("missing state")
    result = wait_for_auth_ok(state)
    print(result)
