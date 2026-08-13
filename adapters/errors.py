"""Connection errors that never include secret values."""

from __future__ import annotations


class AdapterConnectionError(RuntimeError):
    """Raised when connect() or ping() fails for a platform."""

    def __init__(self, platform: str, message: str, *, cause: BaseException | None = None):
        self.platform = platform
        self.cause = cause
        detail = message
        if cause is not None:
            detail = f"{message} ({type(cause).__name__}: {cause})"
        super().__init__(f"[{platform}] {detail}")


def require_value(platform: str, name: str, value: str) -> str:
    if not value or not str(value).strip():
        raise AdapterConnectionError(
            platform,
            f"Missing required environment variable or config: {name}",
        )
    return value.strip()
