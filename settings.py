"""Environment-only configuration; this prototype calls a loopback server."""
import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    base_url: str = "http://127.0.0.1:8080/v1"
    model: str = "gemma-4-12b"
    timeout: float = 120.0

    def __post_init__(self):
        url = urlsplit(self.base_url)
        if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"}
                or url.username or url.password or url.query or url.fragment
                or url.path.rstrip("/") != "/v1"):
            raise ValueError("LLAMA_BASE_URL must be a local HTTP URL ending in /v1.")
        if not self.model.strip() or not 5 <= self.timeout <= 300:
            raise ValueError("Set a model name and a timeout between 5 and 300 seconds.")

    @classmethod
    def from_env(cls):
        return cls(os.getenv("LLAMA_BASE_URL", cls.base_url).rstrip("/"),
                   os.getenv("LLAMA_MODEL", cls.model),
                   float(os.getenv("LLAMA_TIMEOUT", "120")))
