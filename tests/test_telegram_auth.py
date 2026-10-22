import hashlib
import hmac
import json
import unittest
from urllib.parse import urlencode

from telegram_auth import validate_telegram_init_data

TOKEN = "test-token-only-not-a-real-secret"


def signed_data(user_id=123, auth_date=1_700_000_000, **extra):
    values = {
        "auth_date": str(auth_date),
        "query_id": "AAE-test-query",
        "user": json.dumps({"id": user_id, "first_name": "Test"}, separators=(",", ":")),
        **extra,
    }
    check = "\n".join(f"{k}={values[k]}" for k in sorted(values))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


class TelegramAuthTests(unittest.TestCase):
    def test_valid_signed_data_returns_user(self):
        data = signed_data(auth_date=1_700_000_000)
        self.assertEqual(validate_telegram_init_data(data, TOKEN, now=1_700_000_010)["id"], 123)

    def test_tampered_payload_is_rejected(self):
        data = signed_data(auth_date=1_700_000_000).replace("first_name", "last_name")
        with self.assertRaisesRegex(ValueError, "подпись"):
            validate_telegram_init_data(data, TOKEN, now=1_700_000_010)

    def test_expired_data_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "устарел"):
            validate_telegram_init_data(signed_data(auth_date=1_600_000_000), TOKEN, now=1_700_000_000)

    def test_future_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "будущем"):
            validate_telegram_init_data(signed_data(auth_date=1_700_000_100), TOKEN, now=1_700_000_000)

    def test_missing_hash_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "hash"):
            validate_telegram_init_data("auth_date=1700000000", TOKEN, now=1_700_000_000)

    def test_duplicate_parameters_are_rejected(self):
        data = signed_data(auth_date=1_700_000_000) + "&auth_date=1700000000"
        with self.assertRaisesRegex(ValueError, "повторяющиеся"):
            validate_telegram_init_data(data, TOKEN, now=1_700_000_010)

    def test_non_integer_user_id_is_rejected(self):
        values = {"auth_date":"1700000000","user":json.dumps({"id":"not-an-int"})}
        check = "\n".join(f"{k}={values[k]}" for k in sorted(values))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        with self.assertRaisesRegex(ValueError, "id"):
            validate_telegram_init_data(urlencode(values), TOKEN, now=1_700_000_010)


if __name__ == "__main__":
    unittest.main()
