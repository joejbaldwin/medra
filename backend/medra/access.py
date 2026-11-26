"""Access codes and per-code daily budgets for the live DeepSeek source.

The deployed backend spends the group's DeepSeek credit, so a live session
needs an access code. Each code has its own budget of sessions per UTC day.
Replay and paste cost nothing and need no code.

    MEDRA_ACCESS_CODES="profesor:40,grupo:20"   (code:sessions per day)

When the variable is unset (local development) no code is asked for.
Counts live in memory: they reset at UTC midnight and when the process
restarts (Cloud Run starts a new instance after scaling to zero). That is
acceptable here because MEDRA_MAX_TOKENS caps the
cost of each session and MEDRA_LIVE_DISABLED switches live sessions off
entirely; a lost count can only ever give back one day's budget.
"""

from __future__ import annotations

import secrets
import threading
from collections import Counter
from datetime import datetime, timezone

DEFAULT_BUDGET = 20  # sessions per day for a code listed without ":n"


class AccessDenied(Exception):
    """The request may not start a live session. `status` is the HTTP code to return."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def parse_codes(raw: str) -> dict[str, int]:
    """"a:40, b" -> {"a": 40, "b": DEFAULT_BUDGET}. Empty or blank entries are skipped."""
    codes: dict[str, int] = {}
    for entry in raw.split(","):
        code, _, budget = entry.strip().partition(":")
        code = code.strip()
        if not code:
            continue
        codes[code] = int(budget) if budget.strip() else DEFAULT_BUDGET
    return codes


class AccessCodes:
    def __init__(self, budgets: dict[str, int]) -> None:
        self.budgets = dict(budgets)
        self._used: Counter[str] = Counter()
        self._day = self._today()
        self._lock = threading.Lock()  # FastAPI runs sync endpoints in a thread pool

    @property
    def required(self) -> bool:
        return bool(self.budgets)

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def _match(self, code: str) -> str | None:
        # Compare against every code in constant time, so response timing
        # does not reveal how much of a guess was right.
        found = None
        for known in self.budgets:
            if secrets.compare_digest(code.encode(), known.encode()):
                found = known
        return found

    def spend(self, code: str | None) -> None:
        """Use one session of `code`'s budget, or raise AccessDenied."""
        if not self.required:
            return
        known = self._match((code or "").strip())
        if known is None:
            raise AccessDenied(401, "Código de acceso no válido.")
        with self._lock:
            today = self._today()
            if today != self._day:
                self._day, self._used = today, Counter()
            if self._used[known] >= self.budgets[known]:
                raise AccessDenied(
                    429,
                    "Se ha agotado el cupo diario de este código. Las trazas de ejemplo y el texto pegado siguen disponibles.",
                )
            self._used[known] += 1
