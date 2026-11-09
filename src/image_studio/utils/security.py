"""Password hashing and signed browser sessions."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return "$".join(
        (
            "scrypt",
            "16384",
            "8",
            "1",
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, digest_text = encoded.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError, UnicodeError):
        return False
    return hmac.compare_digest(actual, expected)


class SessionCodec:
    """Encode an expiring user session with an HMAC-SHA256 signature."""

    def __init__(self, secret: str, ttl_seconds: int) -> None:
        if len(secret.encode("utf-8")) < 24:
            raise ValueError("SESSION_SECRET must contain at least 24 bytes.")
        self._secret = secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds

    def issue(self, user_id: str, *, now: int | None = None) -> str:
        expiry = (int(time.time()) if now is None else now) + self.ttl_seconds
        payload = f"{user_id}:{expiry}:{secrets.token_urlsafe(12)}".encode()
        encoded = base64.urlsafe_b64encode(payload).rstrip(b"=")
        signature = hmac.new(self._secret, encoded, hashlib.sha256).digest()
        return b".".join(
            (encoded, base64.urlsafe_b64encode(signature).rstrip(b"="))
        ).decode("ascii")

    def read(self, token: str, *, now: int | None = None) -> str | None:
        try:
            encoded, signature_text = token.encode("ascii").split(b".", maxsplit=1)
            supplied_signature = _decode_b64(signature_text)
            expected_signature = hmac.new(
                self._secret, encoded, hashlib.sha256
            ).digest()
            if not hmac.compare_digest(supplied_signature, expected_signature):
                return None
            payload = _decode_b64(encoded).decode("utf-8")
            user_id, expiry_text, nonce = payload.split(":", maxsplit=2)
            expiry = int(expiry_text)
            current_time = int(time.time()) if now is None else now
        except (ValueError, UnicodeError, TypeError):
            return None
        if not user_id or not nonce or expiry <= current_time:
            return None
        return user_id


def _decode_b64(value: bytes) -> bytes:
    return base64.urlsafe_b64decode(value + b"=" * (-len(value) % 4))
