from __future__ import annotations

import hashlib
import hmac
from typing import Optional


class WebhookAuth:
    @staticmethod
    def verify_shared_secret(provided: Optional[str], expected: Optional[str]) -> bool:
        if not expected:
            return True
        return hmac.compare_digest(provided or "", expected)

    @staticmethod
    def verify_hmac(
        body: bytes, signature: Optional[str], secret: Optional[str], prefix: str = "sha256="
    ) -> bool:
        if not secret:
            return True
        if not signature:
            return False
        if prefix and not signature.startswith(prefix):
            return False
        provided = signature[len(prefix) :]
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(provided, digest)
