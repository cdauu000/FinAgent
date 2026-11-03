"""Run-local aliases. UUIDs and source text never become outbound token IDs."""

import secrets
import unicodedata
from collections.abc import Callable
from typing import Literal
from uuid import UUID, uuid4

TOKEN_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
TOKEN_LENGTH = 8


def random_suffix() -> str:
    return "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(TOKEN_LENGTH))


class TokenAllocationError(ValueError):
    pass


class RunTokenAllocator:
    """Not serializable: the 128-bit run ID and local mapping stay inside the process."""

    def __init__(
        self,
        original_query: str,
        *,
        draw: Callable[[], str] = random_suffix,
        max_attempts: int = 32,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("INVALID_TOKEN_ATTEMPT_BUDGET")
        self.run_id: UUID = uuid4()
        self._query = unicodedata.normalize("NFKC", original_query).casefold()
        self._draw = draw
        self._max_attempts = max_attempts
        self._used_suffixes: set[str] = set()
        self._tokens: dict[tuple[str, UUID], str] = {}

    def allocate(self, kind: Literal["ent", "num"], internal_id: UUID) -> str:
        if kind not in {"ent", "num"} or not isinstance(internal_id, UUID):
            raise ValueError("INVALID_INTERNAL_TOKEN_REFERENCE")
        key = (kind, internal_id)
        if key in self._tokens:
            return self._tokens[key]
        for _ in range(self._max_attempts):
            suffix = self._draw()
            if len(suffix) != TOKEN_LENGTH or any(ch not in TOKEN_ALPHABET for ch in suffix):
                raise TokenAllocationError("INVALID_RANDOM_TOKEN_CANDIDATE")
            candidate = f"{kind}_{suffix}"
            if suffix in self._query or candidate in self._query or suffix in self._used_suffixes:
                continue
            self._used_suffixes.add(suffix)
            self._tokens[key] = candidate
            return candidate
        raise TokenAllocationError("TOKEN_COLLISION_BUDGET_EXHAUSTED_LOCAL_ONLY")
