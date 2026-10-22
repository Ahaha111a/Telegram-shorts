"""Pure Telegram Mini App initData verification, isolated for safe unit testing."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def validate_telegram_init_data(init_data: str, bot_token: str, *, now: int | None = None) -> dict:
    if not init_data:
        raise ValueError("Telegram initData отсутствует")
    if not bot_token:
        raise ValueError("BOT_TOKEN не настроен")
    pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=False)
    parsed = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError("В initData обнаружены повторяющиеся параметры")
        parsed[key] = value
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("В initData отсутствует hash")
    if len(received_hash) != 64 or any(c not in "0123456789abcdefABCDEF" for c in received_hash):
        raise ValueError("Некорректный hash Telegram initData")
    data_check_string = "\n".join(f"{key}={parsed[key]}" for key in sorted(parsed))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash.lower()):
        raise ValueError("Неверная подпись Telegram initData")
    try:
        auth_date = int(parsed.get("auth_date", "0"))
    except (TypeError, ValueError):
        raise ValueError("Некорректная временная метка Telegram initData")
    current = int(time.time()) if now is None else int(now)
    if auth_date <= 0:
        raise ValueError("В initData отсутствует auth_date")
    if auth_date > current + 60:
        raise ValueError("Временная метка Telegram initData находится в будущем")
    if current - auth_date > 86400:
        raise ValueError("Telegram initData устарел")
    try:
        user_data = json.loads(parsed.get("user", ""))
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Некорректные данные пользователя Telegram")
    if not isinstance(user_data, dict) or not isinstance(user_data.get("id"), int):
        raise ValueError("Telegram user id отсутствует или некорректен")
    return user_data
